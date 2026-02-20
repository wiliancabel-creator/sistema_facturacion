
import json
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory

from productos.models import Producto

from ventas.models import Venta,DetalleVenta



from django.db.models import Sum
from cai.models import Cai
from ventas.forms import ClienteVentaForm
from ventas.forms import DetalleVentaForm
from datetime import timedelta, date
from cuentas.models import CuentaPorCobrar
from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.db import transaction
from core.utils import monto_en_letras
from configuracion.models import EmpresaConfig


import json
from cotizaciones.models import Cotizacion

from ventas.forms import PagoForm
from ventas.models import Pago
from core.decorators import requiere_modulo
from caja.decorators import requiere_caja_abierta


@login_required
@requiere_modulo('mod_ventas')
@permission_required('ventas.add_venta', raise_exception=True)
@requiere_caja_abierta
def crear_venta(request):   
    DetalleVentaFormSet = formset_factory(
        DetalleVentaForm, extra=0, can_delete=True, min_num=1, validate_min=True
    )
    PagoFormSet = formset_factory(PagoForm, extra=1, min_num=1, validate_min=True)

    preload = None  # ✅ siempre

    if request.method == 'POST':
        cliente_form = ClienteVentaForm(request.POST, empresa=request.empresa)
        formset = DetalleVentaFormSet(request.POST, form_kwargs={'empresa': request.empresa})

        pago_formset = PagoFormSet(request.POST, prefix='pagos')

        # Filtrar formularios válidos
        forms_validos = [
            f for f in formset
            if f.is_valid()
            and f.cleaned_data.get('producto')
            and f.cleaned_data.get('cantidad')
            and f.cleaned_data.get('cantidad') > 0
        ]

        pagos_validos = [
            p for p in pago_formset
            if p.is_valid()
            and p.cleaned_data.get('monto')
            and p.cleaned_data.get('monto') > 0
        ]

        if cliente_form.is_valid() and forms_validos and pagos_validos:
            try:
                with transaction.atomic():
                    venta = cliente_form.save(commit=False)
                    venta.empresa = request.empresa

                    # CAI y número
                    cai_activo = Cai.objects.filter(activo=True, empresa=request.empresa).order_by('-id').first()
                    if cai_activo:
                        correlativo = cai_activo.asignar_siguiente_correlativo()
                        venta.cai = cai_activo
                        venta.numero_factura = cai_activo.get_numero_formateado(correlativo)
                    else:
                        venta.cai = None
                        venta.numero_factura = None

                    # Inicializar totales
                    venta.subtotal_exento = Decimal('0.00')
                    venta.subtotal_g15 = Decimal('0.00')
                    venta.subtotal_g18 = Decimal('0.00')
                    venta.impuesto_15 = Decimal('0.00')
                    venta.impuesto_18 = Decimal('0.00')
                    venta.total = Decimal('0.00')
                    venta.save()

                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    # ✅ Validar stock antes
                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        
                         # 🔒 no permitir productos de otra empresa
                        if producto.empresa_id != request.empresa.id:
                            raise ValueError("❌ Producto inválido para esta empresa.")
                     
                        cantidad = form.cleaned_data['cantidad']
                        if producto.stock < cantidad:
                            raise ValueError(
                                f'❌ Stock insuficiente para {producto.nombre}. '
                                f'Disponible: {producto.stock}, Solicitado: {cantidad}'
                            )

                    # Guardar detalles
                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        cantidad = form.cleaned_data['cantidad']
                        precio_unitario = form.cleaned_data.get('precio_unitario') or producto.precio
                        descuento = form.cleaned_data.get('descuento', 0)

                        detalle = DetalleVenta.objects.create(
                            empresa=request.empresa,
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento
                        )

                        tipo = producto.tipo_impuesto
                        if tipo == 'G15':
                            subtotal_g15 += detalle.subtotal
                            impuesto_15 += detalle.impuesto
                        elif tipo == 'G18':
                            subtotal_g18 += detalle.subtotal
                            impuesto_18 += detalle.impuesto
                        else:
                            subtotal_exento += detalle.subtotal

                        # Reducir stock
                        producto.stock -= cantidad
                        producto.save()

                    venta.subtotal_exento = subtotal_exento
                    venta.subtotal_g15 = subtotal_g15
                    venta.subtotal_g18 = subtotal_g18
                    venta.impuesto_15 = impuesto_15
                    venta.impuesto_18 = impuesto_18
                    venta.total = (
                        subtotal_exento + subtotal_g15 + subtotal_g18 + impuesto_15 + impuesto_18
                    ).quantize(Decimal('0.01'))
                    venta.save()

                    # Validar pagos
                    suma_pagos = sum([p.cleaned_data['monto'] for p in pagos_validos])

                    if venta.tipo_pago == 'contado':
                        if suma_pagos != venta.total:
                            raise ValueError(
                                f'❌ La suma de pagos (L{suma_pagos}) no coincide con el total (L{venta.total}).'
                            )
                    else:
                        if suma_pagos > venta.total:
                            raise ValueError(
                                f'❌ Los abonos (L{suma_pagos}) no pueden ser mayores que el total (L{venta.total}).'
                            )

                    # Guardar pagos SOLO si es CONTADO
                    if venta.tipo_pago == 'contado':
                        for p in pagos_validos:
                            Pago.objects.create(
                                venta=venta,
                                empresa=request.empresa,
                                metodo=p.cleaned_data['metodo'],
                                monto=p.cleaned_data['monto'],
                                referencia=p.cleaned_data.get('referencia') or ''
                            )

                    # Crear cuenta por cobrar si es crédito
                    if venta.tipo_pago.lower() == "credito":
                        if not venta.cliente_id:
                            raise ValueError("❌ Para ventas a crédito debes seleccionar un cliente.")
                        CuentaPorCobrar.objects.create(
                            empresa=request.empresa,
                            cliente=venta.cliente,
                            venta=venta,
                            monto_pendiente=venta.total,
                            monto_pagado=Decimal('0.00'),
                            fecha_vencimiento=date.today() + timedelta(days=30),
                            estado='pendiente'
                        )

                    # ✅ Si venía de cotización, marcarla facturada
                    cot_id = request.session.pop('cotizacion_para_facturar', None)
                    if cot_id:
                        Cotizacion.objects.filter(id=cot_id, empresa=request.empresa).update(estado='facturada')

                    messages.success(
                        request,
                        f'✅ Venta registrada. Factura: {venta.numero_factura} — Total L{venta.total}'
                    )
                    return redirect('ventas:resumen_ventas')

            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'❌ Error al procesar la venta: {e}')

        else:
            if not cliente_form.is_valid():
                messages.error(request, '❌ Error en los datos del cliente.')
            if not forms_validos:
                messages.error(request, '❌ Debe agregar al menos un producto válido.')
            if not pagos_validos:
                messages.error(request, '❌ Debe agregar al menos un pago válido.')

    else:
        # ✅ GET
        cliente_form = ClienteVentaForm(empresa=request.empresa)
        formset = DetalleVentaFormSet(form_kwargs={'empresa': request.empresa})

        pago_formset = PagoFormSet(prefix='pagos')

        # ✅ precarga solo en GET
        from_id = request.GET.get('from_cotizacion', '').strip()
        if from_id.isdigit():
            
            cot = Cotizacion.objects.filter(
                id=int(from_id),
                empresa=request.empresa
            ).prefetch_related('detalles__producto').first()

            if cot and cot.estado != 'facturada':
                preload = {
                    "cotizacion_id": cot.id,
                    "cliente": {
                        "id": cot.cliente_id,
                        "nombre": cot.cliente.nombre if cot.cliente else ""
                    },
                    "tipo_pago": cot.tipo_pago,
                    "productos": [
                        {
                            "id": d.producto_id,
                            "codigo": d.producto.codigo,
                            "codigo_barra": d.producto.codigo_barra or "",
                            "nombre": d.producto.nombre,
                            "stock": d.producto.stock,
                            "cantidad": d.cantidad,
                            "precio_unitario": float(d.precio_unitario),
                            "descuento": float(d.descuento),
                            "tipo_impuesto": d.producto.tipo_impuesto or "E",
                        }
                        for d in cot.detalles.all()
                    ]
                }

    # ✅ ESTE RETURN SIEMPRE SE EJECUTA SI NO HUBO redirect
    productos = Producto.objects.filter(empresa=request.empresa, activo=True).order_by('nombre')
    context = {
        'cliente_form': cliente_form,
        'formset': formset,
        'productos': productos,
        'pago_formset': pago_formset,
        'preload_json': json.dumps(preload) if preload else 'null',
    }
    return render(request, 'ventas/crear_venta.html', context)


from django.core.paginator import Paginator

@login_required
@requiere_modulo('mod_ventas')
@permission_required('ventas.view_venta', raise_exception=True)
def resumen_ventas(request):
    ventas = Venta.objects.filter(empresa=request.empresa).order_by('-fecha')

    # ✅ Filtros (defaults para evitar errores)
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    cliente_id = request.GET.get('cliente_id', '')
    cliente_texto = request.GET.get('cliente_nombre', '')
    tipo_pago = request.GET.get('tipo_pago', '')  # ✅ NUEVO

    # ✅ Rango fechas
    if desde:
        try:
            fecha_desde = datetime.strptime(desde, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date__gte=fecha_desde)
        except ValueError:
            pass

    if hasta:
        try:
            fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date__lte=fecha_hasta)
        except ValueError:
            pass

    # ✅ Cliente seleccionado por autocomplete
    if cliente_id:
        ventas = ventas.filter(cliente_id=cliente_id)

    # ✅ Tipo de pago
    if tipo_pago:
        ventas = ventas.filter(tipo_pago=tipo_pago)

    # ✅ Método de pago
    metodo_pago = request.GET.get('metodo_pago', '')
    if metodo_pago:
        ventas = ventas.filter(pagos__metodo=metodo_pago).distinct()

    total_general = ventas.aggregate(Sum('total'))['total__sum'] or 0

    paginator = Paginator(ventas, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'ventas/resumen_ventas.html', {
        'page_obj': page_obj,
        'total_general': total_general,
        'f': {
            'desde': desde,
            'hasta': hasta,
            'cliente_id': cliente_id,
            'cliente_nombre': cliente_texto,
            'tipo_pago': tipo_pago,
            'metodo_pago': metodo_pago,
        }
    })

@login_required
@requiere_modulo('mod_ventas')
def factura(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id, empresa=request.empresa)
    detalles = DetalleVenta.objects.filter(
    venta=venta,
    empresa=request.empresa
    ).select_related('producto')


    # Fecha de vencimiento para crédito
    fecha_vencimiento = None
    if venta.tipo_pago.lower() == "credito":
        cuenta = venta.cuentaporcobrar.first()
        if cuenta:
            fecha_vencimiento = cuenta.fecha_vencimiento

    # Convertir total a letras
    total_letras = monto_en_letras(venta.total)

    # Obtener configuración del negocio
    try:
        empresa = EmpresaConfig.objects.filter(empresa=request.empresa).first()
    except EmpresaConfig.DoesNotExist:
        empresa = None  # Evita error si aún no han configurado nada

    return render(request, 'ventas/factura.html', {
        'venta': venta,
        'detalles': detalles,
        'fecha_vencimiento': fecha_vencimiento,
        'total_letras': total_letras,
        'empresa': empresa,  #AHORA DISPONIBLE EN EL TEMPLATE
    })
    



   
@login_required
@requiere_modulo('mod_ventas')
@permission_required('productos.view_producto', raise_exception=True)
def buscar_producto(request):
    """
    Busca un producto por ID, código interno, código de barra o nombre parcial.
    """
    codigo = request.GET.get('codigo', '').strip()

    if not codigo:
        return JsonResponse({'encontrado': False, 'error': 'Código vacío'})

    producto = None

    try:
        # 1. Buscar por ID numérico
        if codigo.isdigit():
            producto = Producto.objects.filter(id=int(codigo),empresa=request.empresa,activo=True).first()

        # 2. Buscar por código de barra
        if not producto:
            producto = Producto.objects.filter(codigo_barra=codigo,empresa=request.empresa,activo=True).first()

        # 3. Buscar por código interno
        if not producto:
            producto = Producto.objects.filter(codigo=codigo,empresa=request.empresa, activo=True).first()

        # 4. Buscar por nombre parcial
        if not producto:
            producto = Producto.objects.filter(nombre__icontains=codigo,empresa=request.empresa, activo=True).first()

        if producto:
            return JsonResponse({
                'encontrado': True,
                'id': producto.id,
                'codigo': producto.codigo,
                'codigo_barra': producto.codigo_barra or '',
                'nombre': producto.nombre,
                'precio': str(producto.precio),
                'stock': producto.stock,                         
                'tipo_impuesto': producto.tipo_impuesto
            })

        return JsonResponse({
            'encontrado': False,
            'error': f'Producto "{codigo}" no encontrado'
        })

    except Exception as e:
        return JsonResponse({
            'encontrado': False,
            'error': f'Error en búsqueda: {str(e)}'
        })
   
   
    
@login_required
def buscar_producto_id(request):
    """
    Devuelve datos de un producto a partir de su ID.
    """
    producto_id = request.GET.get('id', '').strip()
    
    if not producto_id.isdigit():
        return JsonResponse({'encontrado': False, 'error': 'ID inválido'})
    
    try:
        producto = Producto.objects.get(id=int(producto_id),empresa=request.empresa,activo=True)
        return JsonResponse({
            'encontrado': True,
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'codigo': producto.codigo,
            'codigo_barra': getattr(producto, 'codigo_barra', '')
        })
    except Producto.DoesNotExist:
        return JsonResponse({'encontrado': False, 'error': 'Producto no encontrado'})
    except Exception as e:
        return JsonResponse({'encontrado': False, 'error': str(e)})    
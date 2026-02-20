
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory


from configuracion.models import EmpresaConfig
from productos.models import Producto

from cotizaciones.forms import CotizacionForm, DetalleCotizacionForm

from cotizaciones.models import Cotizacion, DetalleCotizacion
from clientes.models import Cliente
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from django.http import JsonResponse
from django.db import transaction
from datetime import datetime
from core.decorators import requiere_modulo
from django.core.paginator import Paginator

@login_required
@requiere_modulo('mod_cotizaciones')
@permission_required('cotizaciones.view_cotizacion', raise_exception=True)
def lista_cotizaciones(request):
    cotizaciones = Cotizacion.objects.select_related('cliente').filter(
    empresa=request.empresa
    ).order_by('-fecha')


    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    cliente_id = request.GET.get('cliente_id', '')
    cliente_nombre = request.GET.get('cliente_nombre', '')
    estado = request.GET.get('estado', '')
    tipo_pago = request.GET.get('tipo_pago', '')

    if desde:
        try:
            d = datetime.strptime(desde, '%Y-%m-%d').date()
            cotizaciones = cotizaciones.filter(fecha__date__gte=d)
        except ValueError:
            pass

    if hasta:
        try:
            h = datetime.strptime(hasta, '%Y-%m-%d').date()
            cotizaciones = cotizaciones.filter(fecha__date__lte=h)
        except ValueError:
            pass

    if cliente_id:
        cotizaciones = cotizaciones.filter(cliente_id=cliente_id)

    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)

    if tipo_pago:
        cotizaciones = cotizaciones.filter(tipo_pago=tipo_pago)

    paginator = Paginator(cotizaciones, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'cotizaciones/lista_cotizaciones.html', {
        'page_obj': page_obj,
        'f': {
            'desde': desde,
            'hasta': hasta,
            'cliente_id': cliente_id,
            'cliente_nombre': cliente_nombre,
            'estado': estado,
            'tipo_pago': tipo_pago,
        }
    })

@login_required
@requiere_modulo('mod_cotizaciones')
@permission_required('cotizaciones.add_cotizacion', raise_exception=True)
def crear_cotizacion(request):
    DetalleCotizacionFormSet = formset_factory(DetalleCotizacionForm, extra=0, can_delete=True)
    formset = DetalleCotizacionFormSet(request.POST or None, form_kwargs={'empresa': request.empresa})

    

    if request.method == 'POST':
        cotizacion_form = CotizacionForm(request.POST)
        formset = DetalleCotizacionFormSet(request.POST)

        # cliente por hidden input
        cliente = None
        cliente_id = request.POST.get('cliente_id', '')
        if cliente_id.isdigit():
            cliente = Cliente.objects.filter(id=cliente_id, empresa=request.empresa).first()


        forms_validos = [
            f for f in formset
            if f.is_valid()
            and f.cleaned_data.get('producto')
            and f.cleaned_data.get('cantidad')
            and f.cleaned_data.get('cantidad') > 0
        ]

        if cotizacion_form.is_valid() and cliente and forms_validos:
            try:
                with transaction.atomic():
                    cotizacion = cotizacion_form.save(commit=False)
                    cotizacion.empresa = request.empresa
                    cotizacion.cliente = cliente

                    # init totales
                    cotizacion.subtotal_exento = Decimal('0.00')
                    cotizacion.subtotal_g15 = Decimal('0.00')
                    cotizacion.subtotal_g18 = Decimal('0.00')
                    cotizacion.impuesto_15 = Decimal('0.00')
                    cotizacion.impuesto_18 = Decimal('0.00')
                    cotizacion.total = Decimal('0.00')
                    cotizacion.save()

                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        producto = Producto.objects.filter(id=producto.id, empresa=request.empresa, activo=True).first()
                        if not producto:
                            raise ValueError("Producto inválido para esta empresa.")

                        cantidad = form.cleaned_data['cantidad']
                        precio_unitario = form.cleaned_data.get('precio_unitario') or producto.precio
                        descuento = form.cleaned_data.get('descuento', 0)

                        detalle = DetalleCotizacion.objects.create(
                            empresa=request.empresa,
                            cotizacion=cotizacion,
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

                    cotizacion.subtotal_exento = subtotal_exento
                    cotizacion.subtotal_g15 = subtotal_g15
                    cotizacion.subtotal_g18 = subtotal_g18
                    cotizacion.impuesto_15 = impuesto_15
                    cotizacion.impuesto_18 = impuesto_18
                    cotizacion.total = (
                        subtotal_exento + subtotal_g15 + subtotal_g18 + impuesto_15 + impuesto_18
                    ).quantize(Decimal('0.01'))
                    cotizacion.save()

                    messages.success(request, f'✅ Cotización #{cotizacion.id} creada — Total L{cotizacion.total}')
                    return redirect('cotizaciones:lista_cotizaciones')

            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
        else:
            if not cotizacion_form.is_valid():
                messages.error(request, '❌ Error en tipo de pago.')
            if not cliente:
                messages.error(request, '❌ Debe seleccionar un cliente válido.')
            if not forms_validos:
                messages.error(request, '❌ Debe agregar al menos un producto válido.')

    else:
        cotizacion_form = CotizacionForm()
        formset = DetalleCotizacionFormSet()

    return render(request, 'cotizaciones/crear_cotizacion.html', {
        'cotizacion_form': cotizacion_form,
        'formset': formset,
        'modo_edicion': False,
        'preload_json': json.dumps({"productos": [], "cliente": {"id": "", "nombre": ""}}),
    })



@login_required
@requiere_modulo('mod_cotizaciones')
@permission_required('cotizaciones.change_cotizacion', raise_exception=True)
def editar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, empresa=request.empresa)


    if getattr(cotizacion, 'estado', '') == 'facturada':
        messages.warning(request, "⚠️ Esta cotización ya fue facturada y no se puede editar.")
        return redirect('cotizaciones:lista_cotizaciones')

    DetalleCotizacionFormSet = formset_factory(
        DetalleCotizacionForm, extra=0, can_delete=True, min_num=1, validate_min=True
    )

    # ✅ Preload para JS (cliente + productos)
    preload = {
        "cotizacion_id": cotizacion.id,
        "cliente": {
            "id": cotizacion.cliente_id,
            "nombre": cotizacion.cliente.nombre if cotizacion.cliente else ""
        },
        "tipo_pago": cotizacion.tipo_pago,
        "productos": [
            {
                "id": d.producto_id,
                "codigo": getattr(d.producto, 'codigo', ''),
                "codigo_barra": getattr(d.producto, 'codigo_barra', '') or "",
                "nombre": d.producto.nombre,
                "stock": getattr(d.producto, 'stock', 0),
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario),
                "descuento": float(d.descuento),
                "tipo_impuesto": getattr(d.producto, 'tipo_impuesto', 'E') or "E",
            }
            for d in cotizacion.detalles.select_related('producto').all()
        ]
    }

    if request.method == 'POST':
        cotizacion_form = CotizacionForm(request.POST, instance=cotizacion)
        formset = DetalleCotizacionFormSet(request.POST)

        cliente_id = (request.POST.get('cliente') or '').strip()
        cliente = Cliente.objects.filter(id=cliente_id).first() if cliente_id.isdigit() else None

        forms_validos = [
            f for f in formset
            if f.is_valid()
            and f.cleaned_data.get('producto')
            and f.cleaned_data.get('cantidad')
            and f.cleaned_data.get('cantidad') > 0
        ]

        if cotizacion_form.is_valid() and cliente and forms_validos:
            try:
                with transaction.atomic():
                    # actualizar cabecera
                    cotizacion = cotizacion_form.save(commit=False)
                    cotizacion.cliente = cliente
                    cotizacion.save()

                    # borrar detalles anteriores
                    cotizacion.detalles.filter(empresa=request.empresa).delete()


                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    # recrear detalles
                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        cantidad = form.cleaned_data['cantidad']
                        precio_unitario = form.cleaned_data.get('precio_unitario') or producto.precio
                        descuento = form.cleaned_data.get('descuento', 0)

                        detalle = DetalleCotizacion.objects.create(
                            cotizacion=cotizacion,
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

                    cotizacion.subtotal_exento = subtotal_exento
                    cotizacion.subtotal_g15 = subtotal_g15
                    cotizacion.subtotal_g18 = subtotal_g18
                    cotizacion.impuesto_15 = impuesto_15
                    cotizacion.impuesto_18 = impuesto_18
                    cotizacion.total = (
                        subtotal_exento + subtotal_g15 + subtotal_g18 + impuesto_15 + impuesto_18
                    ).quantize(Decimal('0.01'))
                    cotizacion.save()

                    messages.success(request, f'✅ Cotización #{cotizacion.id} actualizada.')
                    return redirect('cotizaciones:lista_cotizaciones')

            except Exception as e:
                messages.error(request, f'❌ Error al actualizar: {e}')
        else:
            if not cliente:
                messages.error(request, "❌ Debe seleccionar un cliente válido.")
            if not forms_validos:
                messages.error(request, "❌ Debe agregar al menos un producto válido.")
    else:
        cotizacion_form = CotizacionForm(instance=cotizacion)

        # ✅ AQUÍ ESTÁ EL FIX: cargar detalles existentes en el formset
        initial_detalles = [
            {
                'producto': d.producto_id,
                'cantidad': d.cantidad,
                'precio_unitario': d.precio_unitario,
                'descuento': d.descuento,
            }
            for d in cotizacion.detalles.all()
        ]
        formset = DetalleCotizacionFormSet(initial=initial_detalles)

    return render(request, 'cotizaciones/editar_cotizacion.html', {
        'cotizacion_form': cotizacion_form,
        'formset': formset,
        'modo_edicion': True,
        'cotizacion': cotizacion,
        'preload_json': json.dumps(preload),
    })


@login_required
@requiere_modulo('mod_cotizaciones')
@permission_required('ventas.add_venta', raise_exception=True)
def facturar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, empresa=request.empresa)

    if cotizacion.estado == 'facturada':
        # si ya está facturada, solo redirige al resumen de ventas o lista cotizaciones
        return redirect('ventas:resumen_ventas')

    # Guardamos en sesión para marcarla como facturada cuando se complete la venta
    request.session['cotizacion_para_facturar'] = cotizacion.id

    # Redirigir a crear venta con parámetro
    return redirect(f"/ventas/crear/?from_cotizacion={cotizacion.id}")

@login_required
@permission_required('cotizaciones.view_cotizacion', raise_exception=True)
def detalle_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, empresa=request.empresa)
    empresa = EmpresaConfig.objects.filter(empresa=request.empresa).first()


    return render(request, 'cotizaciones/detalle_cotizacion.html', {
        'cotizacion': cotizacion,
        'empresa': empresa,
    })

@login_required
@permission_required('core.delete_cotizacion', raise_exception=True)
def eliminar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id, empresa=request.empresa)

    try:
        cotizacion.delete()
        messages.success(request, f'🗑️ Cotización #{cotizacion_id} eliminada correctamente.')
    except Exception as e:
        messages.error(request, f'❌ Error al eliminar: {str(e)}')

    return redirect('cotizaciones:lista_cotizaciones')


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
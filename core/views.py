from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory
from django.db.models.functions import TruncDay, TruncMonth, ExtractYear
from django.core.serializers.json import DjangoJSONEncoder
import json

from .models import Producto
from .forms import ProductoForm,CategoriaForm
from .models import Venta,DetalleVenta,Compra,DetalleCompra
from .forms import DetalleVentaForm, CotizacionForm, DetalleCotizacionForm
from .forms import ProveedorForm
from .models import Proveedor,Categoria
from .forms import CompraForm, DetalleCompraForm
from django.utils import timezone
from django.db.models import Sum, Q, Max
from .models import Cliente, Cai
from .forms import ClienteForm
from .forms import ClienteVentaForm, CaiForm
from .models import Compra, DetalleCompra
from .models import Venta, DetalleVenta, Cotizacion, DetalleCotizacion
from datetime import timedelta, date
from .models import CuentaPorCobrar, CuentaPorPagar
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.db import transaction
from .utils import monto_en_letras
from .models import EmpresaConfig
from .forms import EmpresaConfigForm


@login_required
@permission_required('core.view_producto', raise_exception=True)
def buscar_producto(request):
    codigo = request.GET.get('codigo')
    try:
        producto = Producto.objects.get(codigo=codigo)
        return JsonResponse({
            'encontrado': True,
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio)
        })
    except Producto.DoesNotExist:
        return JsonResponse({'encontrado': False})



@login_required
@permission_required('core.view_producto', raise_exception=True)
def listar_productos(request):
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')

    productos = Producto.objects.all()

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(codigo__icontains=query) |
            Q(codigo_barra__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    categorias = Categoria.objects.all().order_by('nombre')

    return render(request, 'productos/listar_productos.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_id,
        'query': query
    })




@login_required
@permission_required('core.add_producto', raise_exception=True)
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/agregar_producto.html', {'form': form})



@login_required
@permission_required('core.change_producto', raise_exception=True)
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(request, f"✅ Producto '{producto.nombre}' actualizado correctamente.")
        return redirect('listar_productos')
    return render(request, 'productos/editar_producto.html', {
        'form': form,
        'producto': producto
    })

@login_required
@permission_required('core.delete_producto', raise_exception=True)
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, f"🗑 Producto '{producto.nombre}' eliminado correctamente.")
        return redirect('listar_productos')
    return render(request, 'productos/eliminar_producto.html', {
        'producto': producto
    })


@login_required
@permission_required('core.add_categoria', raise_exception=True)
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Categoría creada correctamente.')
            return redirect('listar_productos')  # Cambia al nombre de tu vista de productos
    else:
        form = CategoriaForm()

    return render(request, 'productos/crear_categoria.html', {'form': form})


@login_required
@permission_required('core.view_cotizacion', raise_exception=True)
def lista_cotizaciones(request):
    cotizaciones = Cotizacion.objects.all().order_by('-fecha')
    return render(request, 'cotizaciones/lista_cotizaciones.html', {'cotizaciones': cotizaciones})

@login_required
@permission_required('core.add_cotizacion', raise_exception=True)
def crear_cotizacion(request):
    DetalleCotizacionFormSet = formset_factory(DetalleCotizacionForm, extra=0, can_delete=True, min_num=1, validate_min=True)

    if request.method == 'POST':
        cotizacion_form = CotizacionForm(request.POST)
        formset = DetalleCotizacionFormSet(request.POST)

        if cotizacion_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = cotizacion_form.save(commit=False)
                    cotizacion.total = Decimal('0.00')
                    cotizacion.save()

                    total_cotizacion = Decimal('0.00')
                    for form in formset:
                        if form.cleaned_data.get('producto'):
                            detalle = form.save(commit=False)
                            detalle.cotizacion = cotizacion
                            detalle.save()
                            total_cotizacion += detalle.subtotal

                    cotizacion.total = total_cotizacion
                    cotizacion.save()

                    messages.success(request, f'✅ Cotización #{cotizacion.id} creada exitosamente.')
                    return redirect('lista_cotizaciones')

            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')

    else:
        cotizacion_form = CotizacionForm()
        formset = DetalleCotizacionFormSet()

    productos = Producto.objects.filter(activo=True).values("id", "nombre", "precio", "codigo", "codigo_barra")
    return render(request, 'cotizaciones/crear_cotizacion.html', {
        'cotizacion_form': cotizacion_form,
        'formset': formset,
        'productos': list(productos),
    })


@login_required
@permission_required('core.change_cotizacion', raise_exception=True)
def editar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_id)
    DetalleCotizacionFormSet = formset_factory(DetalleCotizacionForm, extra=0, can_delete=True)

    if request.method == 'POST':
        cotizacion_form = CotizacionForm(request.POST, instance=cotizacion)
        formset = DetalleCotizacionFormSet(request.POST)

        if cotizacion_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    cotizacion = cotizacion_form.save(commit=False)
                    cotizacion.total = Decimal('0.00')
                    cotizacion.save()

                    # Borrar detalles anteriores y volver a crearlos
                    cotizacion.detalles.all().delete()
                    total_cotizacion = Decimal('0.00')

                    for form in formset:
                        if form.cleaned_data.get('producto'):
                            detalle = form.save(commit=False)
                            detalle.cotizacion = cotizacion
                            detalle.save()
                            total_cotizacion += detalle.subtotal

                    cotizacion.total = total_cotizacion
                    cotizacion.save()

                    messages.success(request, f'✏️ Cotización #{cotizacion.id} editada exitosamente.')
                    return redirect('lista_cotizaciones')

            except Exception as e:
                messages.error(request, f'❌ Error al editar: {str(e)}')
    else:
        cotizacion_form = CotizacionForm(instance=cotizacion)
        # Prellenar formset con los detalles existentes
        initial_data = [{
            'producto': d.producto.id,
            'cantidad': d.cantidad,
            'precio_unitario': d.precio_unitario,
            'descuento': d.descuento
        } for d in cotizacion.detalles.all()]
        DetalleCotizacionFormSet = formset_factory(DetalleCotizacionForm, extra=0, can_delete=True)
        formset = DetalleCotizacionFormSet(initial=initial_data)

    productos = Producto.objects.filter(activo=True).values("id", "nombre", "precio", "codigo", "codigo_barra")
    return render(request, 'cotizaciones/editar_cotizacion.html', {
        'cotizacion_form': cotizacion_form,
        'formset': formset,
        'productos': list(productos),
        'cotizacion': cotizacion,
    })


@login_required
@permission_required('core.add_venta', raise_exception=True)
def facturar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_id)

    if cotizacion.estado == "facturada":
        messages.warning(request, "Esta cotización ya fue facturada.")
        return redirect('lista_cotizaciones')

    try:
        with transaction.atomic():
            # Crear la venta a partir de la cotización
            venta = Venta.objects.create(
                cliente=cotizacion.cliente,
                total=cotizacion.total,
                tipo_pago="contado"  # o según lo definas
            )

            for detalle in cotizacion.detalles.all():
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    descuento=detalle.descuento
                )

                # Descontar stock
                detalle.producto.stock -= detalle.cantidad
                detalle.producto.save()

            cotizacion.estado = "facturada"
            cotizacion.save()

            messages.success(request, f'✅ Cotización #{cotizacion.id} facturada como Venta #{venta.id}.')
            return redirect('resumen_ventas')

    except Exception as e:
        messages.error(request, f'❌ Error al facturar la cotización: {str(e)}')
    return render(request, 'crear_cotizacion.html')


@login_required
@permission_required('core.add_cotizacion', raise_exception=True)
def detalle_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_id)
    return render(request, 'cotizaciones/detalle_cotizacion.html', {
        'cotizacion': cotizacion
    })

@login_required
@permission_required('core.delete_cotizacion', raise_exception=True)
def eliminar_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, pk=cotizacion_id)

    try:
        cotizacion.delete()
        messages.success(request, f'🗑️ Cotización #{cotizacion_id} eliminada correctamente.')
    except Exception as e:
        messages.error(request, f'❌ Error al eliminar: {str(e)}')

    return redirect('lista_cotizaciones')


from .forms import PagoForm
from .models import Pago

@login_required
@permission_required('core.add_venta', raise_exception=True)
def crear_venta(request):
    DetalleVentaFormSet = formset_factory(DetalleVentaForm, extra=0, can_delete=True, min_num=1, validate_min=True)
    PagoFormSet = formset_factory(PagoForm, extra=1, min_num=1, validate_min=True)

    if request.method == 'POST':
        cliente_form = ClienteVentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)
        pago_formset = PagoFormSet(request.POST, prefix='pagos')

        # Filtrar formularios válidos
        forms_validos = [
            f for f in formset
            if f.is_valid()
            and f.cleaned_data.get('producto')
            and f.cleaned_data.get('cantidad')
            and f.cleaned_data.get('cantidad') > 0
        ]

        pagos_validos = [p for p in pago_formset if p.is_valid() and p.cleaned_data.get('monto') and p.cleaned_data.get('monto') > 0]

        if cliente_form.is_valid() and forms_validos and pagos_validos:
            try:
                with transaction.atomic():
                    venta = cliente_form.save(commit=False)

                    # CAI y número
                    cai_activo = Cai.objects.filter(activo=True).order_by('-id').first()
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

                    # Calcular totales
                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    # ✅ PRIMERO: Validar stock ANTES de crear detalles
                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        cantidad = form.cleaned_data['cantidad']
                        
                        if producto.stock < cantidad:
                            # ✅ Lanzar excepción DENTRO del atomic
                            raise ValueError(f'❌ Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}, Solicitado: {cantidad}')

                    # Guardar detalles
                    for form in forms_validos:
                        producto = form.cleaned_data['producto']
                        cantidad = form.cleaned_data['cantidad']
                        precio_unitario = form.cleaned_data.get('precio_unitario') or producto.precio
                        descuento = form.cleaned_data.get('descuento', 0)

                        detalle = DetalleVenta.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento
                        )

                        tipo = producto.tipo_impuesto
                        if tipo == 'G15':
                            subtotal_g15 += detalle.subtotal
                            impuesto_15 += detalle.impuesto if hasattr(detalle, 'impuesto') else (detalle.subtotal * Decimal('0.15'))
                        elif tipo == 'G18':
                            subtotal_g18 += detalle.subtotal
                            impuesto_18 += detalle.impuesto if hasattr(detalle, 'impuesto') else (detalle.subtotal * Decimal('0.18'))
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
                    venta.total = (subtotal_exento + subtotal_g15 + subtotal_g18 + impuesto_15 + impuesto_18).quantize(Decimal('0.01'))
                    venta.save()

                    # Validar pagos
                    suma_pagos = sum([p.cleaned_data['monto'] for p in pagos_validos])
                    if suma_pagos != venta.total:
                        raise ValueError(f'❌ La suma de pagos (L{suma_pagos}) no coincide con el total (L{venta.total}).')

                    # Guardar pagos
                    for p in pagos_validos:
                        Pago.objects.create(
                            venta=venta,
                            metodo=p.cleaned_data['metodo'],
                            monto=p.cleaned_data['monto'],
                            referencia=p.cleaned_data.get('referencia') or ''
                        )

                    # Crear cuenta por cobrar si es crédito
                    if venta.tipo_pago.lower() == "credito":
                        CuentaPorCobrar.objects.create(
                            cliente=venta.cliente,
                            venta=venta,
                            monto_pendiente=venta.total,
                            fecha_vencimiento=date.today() + timedelta(days=30),
                            estado='pendiente'
                        )

                    messages.success(request, f'✅ Venta registrada. Factura: {venta.numero_factura} — Total L{venta.total}')
                    return redirect('resumen_ventas')

            except ValueError as e:
                # ✅ Capturar el error y mostrar mensaje amigable
                messages.error(request, str(e))
            except Exception as e:
                # ✅ Cualquier otro error
                messages.error(request, f'❌ Error al procesar la venta: {e}')

        else:
            if not cliente_form.is_valid():
                messages.error(request, '❌ Error en los datos del cliente.')
            if not forms_validos:
                messages.error(request, '❌ Debe agregar al menos un producto válido.')
            if not pagos_validos:
                messages.error(request, '❌ Debe agregar al menos un pago válido.')

    else:
        cliente_form = ClienteVentaForm()
        formset = DetalleVentaFormSet()
        pago_formset = PagoFormSet(prefix='pagos')

    productos = Producto.objects.filter(activo=True).order_by('nombre')
    context = {
        'cliente_form': cliente_form,
        'formset': formset,
        'productos': productos,
        'pago_formset': pago_formset,
    }
    return render(request, 'crear_venta.html', context)


@login_required
@permission_required('core.view_venta', raise_exception=True)
def resumen_ventas(request):
    fecha_str = request.GET.get('fecha')
    ventas = []
    total_general = 0

    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            ventas = Venta.objects.filter(fecha__date=fecha).order_by('-fecha')
        except ValueError:
            ventas = Venta.objects.none()
    else:
        # ✅ Mostrar todas las ventas si no se selecciona fecha
        ventas = Venta.objects.all().order_by('-fecha')

    total_general = ventas.aggregate(Sum('total'))['total__sum'] or 0

    return render(request, 'resumen_ventas.html', {
        'ventas': ventas,
        'total_general': total_general,
        'fecha': fecha_str
    })

@login_required
@permission_required('core.view_compra', raise_exception=True)
def resumen_compras(request):
    fecha = request.GET.get('fecha')

    compras = Compra.objects.all().order_by('-fecha')

    if fecha:
        compras = compras.filter(fecha__date=fecha)

    total_general = compras.aggregate(Sum('total'))['total__sum'] or 0

    return render(request, 'resumen_compras.html', {
        'compras': compras,
        'total_general': total_general,
        'fecha': fecha
    })
    

@login_required
def factura(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('producto')

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
        empresa = EmpresaConfig.objects.get(pk=1)
    except EmpresaConfig.DoesNotExist:
        empresa = None  # Evita error si aún no han configurado nada

    return render(request, 'factura.html', {
        'venta': venta,
        'detalles': detalles,
        'fecha_vencimiento': fecha_vencimiento,
        'total_letras': total_letras,
        'empresa': empresa,  # 👈 AHORA DISPONIBLE EN EL TEMPLATE
    })



@login_required
@permission_required('core.add_compra', raise_exception=True)
def crear_compra(request):
    if request.method == 'POST':
        compra_form = CompraForm(request.POST)

        # Acepta ambas convenciones: con [] y sin []
        productos_ids = request.POST.getlist('producto_id[]') or request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad[]') or request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio_unitario[]') or request.POST.getlist('precio_unitario')

        # Normalizar y filtrar vacíos/invalidos
        productos_validos = []
        for pid, cant, precio in zip(productos_ids, cantidades, precios):
            pid = (pid or '').strip()
            cant = (cant or '').strip()
            precio = (precio or '').strip()
            if not pid or not cant or not precio:
                continue
            try:
                cantidad = int(cant)
                if cantidad <= 0:
                    continue
                # Soportar coma decimal
                precio_unitario = Decimal(precio.replace(',', '.'))
            except (ValueError, InvalidOperation):
                continue
            productos_validos.append((pid, cantidad, precio_unitario))

        if compra_form.is_valid() and productos_validos:
            try:
                with transaction.atomic():
                    compra = compra_form.save(commit=False)
                    # Asegurar tipo_pago
                    compra.tipo_pago = compra_form.cleaned_data.get('tipo_pago')
                    compra.total = Decimal('0.00')
                    compra.save()

                    total = Decimal('0.00')

                    for pid, cantidad, precio_unitario in productos_validos:
                        producto = Producto.objects.get(id=pid)
                        subtotal = precio_unitario * cantidad

                        DetalleCompra.objects.create(
                            compra=compra,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            subtotal=subtotal
                        )

                        # Actualizar stock
                        producto.stock += cantidad
                        producto.save()

                        total += subtotal

                    compra.total = total
                    compra.save()

                    if compra.tipo_pago == 'credito':
                        CuentaPorPagar.objects.create(
                            proveedor=compra.proveedor,
                            compra=compra,
                            monto_pendiente=compra.total,
                            fecha_vencimiento=compra.fecha + timedelta(days=30),
                            estado='pendiente'
                        )

                    # Contar productos distintos en la compra
                    cantidad_productos = len(productos_validos)
                    messages.success(
                        request,
                        f"✅ Compra a {compra.proveedor} registrada exitosamente – "
                        f"Total: L{compra.total:.2f} – {cantidad_productos} producto(s)"
                    )
                    return redirect('resumen_compra', compra_id=compra.id)

            except Exception as e:
                messages.error(request, f"❌ Error al registrar la compra: {str(e)}")

        else:
            if not compra_form.is_valid():
                messages.error(request, "Error en datos de la compra.")
            if not productos_validos:
                messages.error(request, "Debe agregar al menos un producto válido.")

    else:
        compra_form = CompraForm()

    productos = Producto.objects.all()
    return render(request, 'crear_compra.html', {
        'compra_form': compra_form,
        'productos': productos
    })




@login_required
@permission_required('core.view_compra', raise_exception=True)
def resumen_compra(request, compra_id):
    compra = Compra.objects.get(id=compra_id)
    detalles = DetalleCompra.objects.filter(compra=compra)
    return render(request, 'resumen_compra.html', {'compra': compra, 'detalles': detalles})

@login_required
@permission_required('core.add_proveedor', raise_exception=True)
def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/registrar.html', {'form': form})

@login_required
@permission_required('core.view_proveedor', raise_exception=True)
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/lista.html', {'proveedores': proveedores})

@login_required
def dashboard(request):
    hoy = timezone.localdate()

    ventas_hoy = Venta.objects.filter(fecha__date=hoy).aggregate(total=Sum('total'))['total'] or 0
    compras_hoy = Compra.objects.filter(fecha__date=hoy).aggregate(total=Sum('total'))['total'] or 0

    productos_vendidos_hoy = DetalleVenta.objects.filter(venta__fecha__date=hoy).aggregate(cantidad=Sum('cantidad'))['cantidad'] or 0
    productos_comprados_hoy = DetalleCompra.objects.filter(compra__fecha__date=hoy).aggregate(cantidad=Sum('cantidad'))['cantidad'] or 0

    total_ventas = Venta.objects.aggregate(total=Sum('total'))['total'] or 0
    total_compras = Compra.objects.aggregate(total=Sum('total'))['total'] or 0

    total_productos = Producto.objects.count()
    total_clientes = Cliente.objects.count()
    total_proveedores = Proveedor.objects.count()

    context = {
        'ventas_hoy': ventas_hoy,
        'compras_hoy': compras_hoy,
        'productos_vendidos_hoy': productos_vendidos_hoy,
        'productos_comprados_hoy': productos_comprados_hoy,
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
    }

    return render(request, 'dashboard.html', context)

@login_required
@permission_required('core.view_cliente', raise_exception=True)
def listar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/listar_clientes.html', {'clientes': clientes})

@login_required
@permission_required('core.add_cliente', raise_exception=True)
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})


@login_required
@permission_required('core.view_venta', raise_exception=True)
def dashboard_graficos(request):
    # Ventas por día (últimos 30 días)
    ventas_diarias = (
        Venta.objects.annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('total'))
        .order_by('dia')
    )

    compras_diarias = (
        Compra.objects.annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('total'))
        .order_by('dia')
    )

    # Ventas y compras por mes
    ventas_mensuales = (
        Venta.objects.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    compras_mensuales = (
        Compra.objects.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    # Ventas y compras por año
    ventas_anuales = (
        Venta.objects.annotate(año=ExtractYear('fecha'))
        .values('año')
        .annotate(total=Sum('total'))
        .order_by('año')
    )

    compras_anuales = (
        Compra.objects.annotate(año=ExtractYear('fecha'))
        .values('año')
        .annotate(total=Sum('total'))
        .order_by('año')
    )

    context = {
        'ventas_diarias': json.dumps(list(ventas_diarias), cls=DjangoJSONEncoder),
        'compras_diarias': json.dumps(list(compras_diarias), cls=DjangoJSONEncoder),
        'ventas_mensuales': json.dumps(list(ventas_mensuales), cls=DjangoJSONEncoder),
        'compras_mensuales': json.dumps(list(compras_mensuales), cls=DjangoJSONEncoder),
        'ventas_anuales': json.dumps(list(ventas_anuales), cls=DjangoJSONEncoder),
        'compras_anuales': json.dumps(list(compras_anuales), cls=DjangoJSONEncoder),
    }

    return render(request, 'dashboard_graficos.html', context)


@login_required
@permission_required('core.view_cuentaporcobrar', raise_exception=True)
@permission_required('core.view_cuentaporpagar', raise_exception=True)
def resumen_cuentas(request):
    estado = request.GET.get('estado')  # puede ser 'pendiente', 'pagado' o None

    por_cobrar = CuentaPorCobrar.objects.all()
    por_pagar = CuentaPorPagar.objects.all()

    if estado:
        por_cobrar = por_cobrar.filter(estado=estado)
        por_pagar = por_pagar.filter(estado=estado)

    return render(request, 'resumen_cuentas.html', {
        'por_cobrar': por_cobrar,
        'por_pagar': por_pagar,
        'estado_seleccionado': estado
    })
    

@login_required
@permission_required('core.change_cuentaporcobrar', raise_exception=True)
def registrar_pago_cliente(request, cuenta_id):
    cuenta = get_object_or_404(CuentaPorCobrar, id=cuenta_id)

    # Calculamos cuánto resta por pagar
    restante = cuenta.monto_pendiente - cuenta.monto_pagado

    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto'))

        # Validación: no puede pagar más de lo que resta
        if monto > restante:
            messages.error(
                request,
                f"No podés pagar más de L {restante:.2f}. Ingresa un monto válido."
            )
            return render(request, 'registrar_pago_cliente.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        # Registro del pago
        cuenta.monto_pagado += monto
        cuenta.fecha_pago = timezone.now().date()

        # Si cubrimos o excedemos el total, marcamos como pagado
        if cuenta.monto_pagado >= cuenta.monto_pendiente:
            cuenta.estado = 'pagado'

        cuenta.save()
        return redirect('resumen_cuentas')

    # GET: muestro el formulario
    return render(request, 'registrar_pago_cliente.html', {
        'cuenta': cuenta,
        'restante': restante
    })


@login_required
@permission_required('core.change_cuentaporpagar', raise_exception=True)
def registrar_pago_proveedor(request, cuenta_id):
    cuenta = get_object_or_404(CuentaPorPagar, id=cuenta_id)

    # Calculamos cuánto resta por pagar
    restante = cuenta.monto_pendiente - cuenta.monto_pagado

    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto'))

        # Validación: no puede pagar más de lo que resta
        if monto > restante:
            messages.error(
                request,
                f"No podés pagar más de L {restante:.2f}. Ingresa un monto válido."
            )
            return render(request, 'registrar_pago_proveedor.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        # Registrar el pago
        cuenta.monto_pagado += monto
        cuenta.fecha_pago = timezone.now().date()

        # Si cubrimos o excedemos el total, marcamos como pagado
        if cuenta.monto_pagado >= cuenta.monto_pendiente:
            cuenta.estado = 'pagado'

        cuenta.save()
        return redirect('resumen_cuentas')

    # Si es GET, mostramos el formulario con el saldo restante
    return render(request, 'registrar_pago_proveedor.html', {
        'cuenta': cuenta,
        'restante': restante
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username} 👋')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html')
    
@login_required
@permission_required('core.view_cai')
def listar_cai(request):
    cais = Cai.objects.all().order_by('-activo', 'fecha_limite')
    return render(request, 'cai/listar_cai.html', {'cais': cais})

@login_required
@permission_required('core.add_cai')
def crear_cai(request):
    form = CaiForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('listar_cai')
    return render(request, 'cai/crear_cai.html', {'form': form})

@login_required
@permission_required('core.change_cai')
def editar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk)
    form = CaiForm(request.POST or None, instance=cai)
    if form.is_valid():
        form.save()
        return redirect('listar_cai')
    return render(request, 'cai/editar_cai.html', {'form': form})

@login_required
@permission_required('core.delete_cai')
def eliminar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk)
    cai.delete()
    return redirect('listar_cai')


from django.http import JsonResponse
from .models import Producto

@login_required
def buscar_producto(request):
    """
    Busca un producto por código de barra, ID, código interno o nombre parcial.
    """
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({'encontrado': False, 'error': 'Código vacío'})
    
    producto = None
    
    try:
        # 1. Buscar por ID numérico
        if codigo.isdigit():
            producto = Producto.objects.filter(id=int(codigo), activo=True).first()
        
        # 2. Buscar por código de barra
        if not producto:
            producto = Producto.objects.filter(codigo_barra=codigo, activo=True).first()
        
        # 3. Buscar por código interno
        if not producto:
            producto = Producto.objects.filter(codigo=codigo, activo=True).first()
        
        # 4. Buscar por nombre parcial
        if not producto:
            producto = Producto.objects.filter(nombre__icontains=codigo, activo=True).first()
        
        if producto:
            return JsonResponse({
                'encontrado': True,
            'id': producto.id,
            'codigo': producto.codigo,
            'codigo_barra': producto.codigo_barra or '', 
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'tipo_impuesto': producto.tipo_impuesto
       })
        else:
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
        producto = Producto.objects.get(id=int(producto_id), activo=True)
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
    
    
@login_required
def buscar_clientes(request):
    term = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nombre__icontains=term).values('id', 'nombre')[:20]
    results = [
        {"id": c["id"], "text": f"{c['id']} - {c['nombre']}"}
        for c in clientes
    ]
    return JsonResponse({"results": results})
    
    
    
from .models import Empleado, PagoEmpleado
from .forms import EmpleadoForm, PagoEmpleadoForm

# Listado de empleados
@login_required
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, "empleados/lista_empleados.html", {"empleados": empleados})

# Crear empleado
@login_required
def crear_empleado(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado registrado correctamente")
            return redirect("lista_empleados")
    else:
        form = EmpleadoForm()
    return render(request, "empleados/empleado_form.html", {"form": form})

# Editar empleado
@login_required
def editar_empleado(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado actualizado correctamente")
            return redirect("lista_empleados")
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, "empleados/empleado_form.html", {"form": form})

# Registrar pago
@login_required
def registrar_pago(request):
    if request.method == "POST":
        form = PagoEmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago registrado correctamente")
            return redirect("lista_pagos")
    else:
        form = PagoEmpleadoForm()

    # 👇 Diccionario {id_empleado: salario_base}
    salarios = {e.id: float(e.salario_base) for e in Empleado.objects.all()}

    return render(request, "empleados/pago_form.html", {
        "form": form,
        "salarios": salarios
    })

# Listado de pagos
@login_required
def lista_pagos(request):
    pagos = PagoEmpleado.objects.select_related("empleado").order_by("-fecha_pago")
    return render(request, "empleados/lista_pagos.html", {"pagos": pagos})


@login_required
@permission_required('core.change_cai')
def configuracion_empresa(request):
    try:
        config = EmpresaConfig.objects.get(pk=1)
    except EmpresaConfig.DoesNotExist:
        config = EmpresaConfig(pk=1)

    if request.method == 'POST':
        form = EmpresaConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración guardada correctamente.")
            return redirect('configuracion_empresa')
    else:
        form = EmpresaConfigForm(instance=config)

    return render(request, 'configuracion_empresa.html', {'form': form})

from .models import models
@login_required
def sugerencias_productos(request):
    """
    Devuelve sugerencias de productos mientras el usuario escribe.
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # Solo buscar si escribe al menos 2 caracteres
        return JsonResponse({'productos': []})
    
    try:
        # Buscar en código, código de barra y nombre
        productos = Producto.objects.filter(
            activo=True
        ).filter(
            models.Q(codigo__icontains=query) |
            models.Q(codigo_barra__icontains=query) |
            models.Q(nombre__icontains=query)
        )[:10]  # Máximo 10 sugerencias
        
        resultados = [{
            'id': p.id,
            'codigo': p.codigo,
            'codigo_barra': p.codigo_barra or '',
            'nombre': p.nombre,
            'precio': str(p.precio),
            'stock': p.stock,
            'tipo_impuesto': p.tipo_impuesto,
            'display': f"{p.codigo} - {p.nombre} (Stock: {p.stock})"  # Texto para mostrar
        } for p in productos]
        
        return JsonResponse({'productos': resultados})
        
    except Exception as e:
        return JsonResponse({'productos': [], 'error': str(e)})
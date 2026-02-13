
from django.shortcuts import render, redirect


from productos.models import Producto

from compras.models import Compra,DetalleCompra


from compras.forms import CompraForm

from django.db.models import Sum



from datetime import timedelta
from cuentas.models import CuentaPorPagar
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from django.db import transaction

from core.decorators import requiere_modulo
from caja.decorators import requiere_caja_abierta


@login_required
@requiere_modulo('mod_compras')
@permission_required('compras.add_compra', raise_exception=True)
@requiere_caja_abierta
def crear_compra(request):
    if request.method == 'POST':
        compra_form = CompraForm(request.POST)

        # Obtener arrays de productos
        productos_ids = request.POST.getlist('producto_id[]') or request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad[]') or request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio_unitario[]') or request.POST.getlist('precio_unitario')
        descuentos = request.POST.getlist('descuento[]') or request.POST.getlist('descuento')

        # Validar y normalizar
        productos_validos = []
        for i, (pid, cant, precio, desc) in enumerate(zip(productos_ids, cantidades, precios, descuentos)):
            pid = (pid or '').strip()
            cant = (cant or '').strip()
            precio = (precio or '').strip()
            desc = (desc or '0').strip()
            
            if not pid or not cant or not precio:
                continue
            try:
                cantidad = int(cant)
                if cantidad <= 0:
                    continue
                precio_unitario = Decimal(precio.replace(',', '.'))
                descuento = Decimal(desc.replace(',', '.'))
            except (ValueError, InvalidOperation):
                continue
            
            productos_validos.append((pid, cantidad, precio_unitario, descuento))

        if compra_form.is_valid() and productos_validos:
            try:
                with transaction.atomic():
                    compra = compra_form.save(commit=False)
                    compra.usuario = request.user  # ✅ Registrar quién hizo la compra
                    
                    # Inicializar totales
                    compra.subtotal_exento = Decimal('0.00')
                    compra.subtotal_g15 = Decimal('0.00')
                    compra.subtotal_g18 = Decimal('0.00')
                    compra.impuesto_15 = Decimal('0.00')
                    compra.impuesto_18 = Decimal('0.00')
                    compra.total = Decimal('0.00')
                    compra.save()

                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    # Procesar cada producto
                    for pid, cantidad, precio_unitario, descuento in productos_validos:
                        producto = Producto.objects.get(id=pid)
                        
                        # Calcular subtotal con descuento
                        base = precio_unitario * cantidad
                        descuento_monto = base * (descuento / Decimal('100'))
                        subtotal_linea = base - descuento_monto

                        # Crear detalle
                        detalle = DetalleCompra.objects.create(
                            compra=compra,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento,
                            subtotal=subtotal_linea
                        )

                        # Clasificar por tipo de impuesto
                        tipo = producto.tipo_impuesto
                        if tipo == 'G15':
                            subtotal_g15 += subtotal_linea
                            impuesto_15 += (subtotal_linea * Decimal('0.15'))
                        elif tipo == 'G18':
                            subtotal_g18 += subtotal_linea
                            impuesto_18 += (subtotal_linea * Decimal('0.18'))
                        else:
                            subtotal_exento += subtotal_linea

                        # Actualizar stock
                        producto.stock += cantidad
                        producto.save()

                    # Guardar totales en la compra
                    compra.subtotal_exento = subtotal_exento
                    compra.subtotal_g15 = subtotal_g15
                    compra.subtotal_g18 = subtotal_g18
                    compra.impuesto_15 = impuesto_15
                    compra.impuesto_18 = impuesto_18
                    compra.total = (subtotal_exento + subtotal_g15 + subtotal_g18 + 
                                   impuesto_15 + impuesto_18).quantize(Decimal('0.01'))
                    compra.save()

                    # Crear cuenta por pagar si es crédito
                    if compra.tipo_pago == 'credito':
                        CuentaPorPagar.objects.create(
                            proveedor=compra.proveedor,
                            compra=compra,
                            monto_pendiente=compra.total,
                            fecha_vencimiento=compra.fecha.date() + timedelta(days=30),
                            estado='pendiente'
                        )

                    messages.success(
                        request,
                        f"✅ Compra #{compra.numero_compra} registrada exitosamente – "
                        f"Total: L{compra.total:.2f} – {len(productos_validos)} producto(s)"
                    )
                    return redirect('compras:resumen_compra', compra_id=compra.id)

            except Exception as e:
                messages.error(request, f"❌ Error al registrar la compra: {str(e)}")

        else:
            if not compra_form.is_valid():
                messages.error(request, "Error en datos de la compra.")
            if not productos_validos:
                messages.error(request, "Debe agregar al menos un producto válido.")

    else:
        compra_form = CompraForm()

    productos = Producto.objects.filter(activo=True).order_by('nombre')
    return render(request, 'compras/crear_compra.html', {
        'compra_form': compra_form,
        'productos': productos
    })



@login_required
@requiere_modulo('mod_compras')
@permission_required('compras.view_compra', raise_exception=True)
def resumen_compra(request, compra_id):
    compra = Compra.objects.get(id=compra_id)
    detalles = DetalleCompra.objects.filter(compra=compra)
    return render(request, 'compras/resumen_compra.html', {'compra': compra, 'detalles': detalles})


@login_required
@requiere_modulo('mod_compras')
@permission_required('compras.view_compras', raise_exception=True)
def resumen_compras(request):
    compras = Compra.objects.all().order_by('-fecha')

    # ✅ filtros
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    proveedor_id = request.GET.get('proveedor_id', '')
    proveedor_nombre = request.GET.get('proveedor_nombre', '')

    # ✅ rango fechas
    if desde:
        try:
            fecha_desde = datetime.strptime(desde, '%Y-%m-%d').date()
            compras = compras.filter(fecha__date__gte=fecha_desde)
        except ValueError:
            pass

    if hasta:
        try:
            fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d').date()
            compras = compras.filter(fecha__date__lte=fecha_hasta)
        except ValueError:
            pass

    # ✅ proveedor por ID (autocompletado)
    if proveedor_id:
        compras = compras.filter(proveedor_id=proveedor_id)

    total_general = compras.aggregate(Sum('total'))['total__sum'] or 0

    return render(request, 'compras/resumen_compras.html', {
        'compras': compras,
        'total_general': total_general,
        'f': {
            'desde': desde,
            'hasta': hasta,
            'proveedor_id': proveedor_id,
            'proveedor_nombre': proveedor_nombre,
        }
    })






   
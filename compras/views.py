from django.shortcuts import render, redirect
from productos.models import Producto
from compras.models import Compra, DetalleCompra
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
        compra_form = CompraForm(request.POST, empresa=request.empresa)

        productos_ids = request.POST.getlist('producto_id[]') or request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad[]') or request.POST.getlist('cantidad')
        precios = request.POST.getlist('precio_unitario[]') or request.POST.getlist('precio_unitario')
        descuentos = request.POST.getlist('descuento[]') or request.POST.getlist('descuento')

        productos_validos = []
        for pid, cant, precio, desc in zip(productos_ids, cantidades, precios, descuentos):
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
                    compra.empresa = request.empresa  # ✅ MULTI-TENANT
                    compra.usuario = request.user
                    compra.save()

                    subtotal_exento = Decimal('0.00')
                    subtotal_g15 = Decimal('0.00')
                    subtotal_g18 = Decimal('0.00')
                    impuesto_15 = Decimal('0.00')
                    impuesto_18 = Decimal('0.00')

                    for pid, cantidad, precio_unitario, descuento in productos_validos:
                        # ✅ MULTI-TENANT producto
                        producto = Producto.objects.get(id=pid, empresa=request.empresa)

                        base = precio_unitario * cantidad
                        descuento_monto = base * (descuento / Decimal('100'))
                        subtotal_linea = base - descuento_monto

                        DetalleCompra.objects.create(
                            empresa=request.empresa,   # ✅ MULTI-TENANT
                            compra=compra,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento=descuento,
                            subtotal=subtotal_linea
                        )

                        tipo = producto.tipo_impuesto
                        if tipo == 'G15':
                            subtotal_g15 += subtotal_linea
                            impuesto_15 += (subtotal_linea * Decimal('0.15'))
                        elif tipo == 'G18':
                            subtotal_g18 += subtotal_linea
                            impuesto_18 += (subtotal_linea * Decimal('0.18'))
                        else:
                            subtotal_exento += subtotal_linea

                        producto.stock += cantidad
                        producto.save()

                    compra.subtotal_exento = subtotal_exento
                    compra.subtotal_g15 = subtotal_g15
                    compra.subtotal_g18 = subtotal_g18
                    compra.impuesto_15 = impuesto_15
                    compra.impuesto_18 = impuesto_18
                    compra.total = (subtotal_exento + subtotal_g15 + subtotal_g18 + impuesto_15 + impuesto_18).quantize(Decimal('0.01'))
                    compra.save()

                    if compra.tipo_pago == 'credito':
                        CuentaPorPagar.objects.create(
                            empresa=request.empresa,   # ✅ MULTI-TENANT
                            proveedor=compra.proveedor,
                            compra=compra,
                            monto_pendiente=compra.total,
                            fecha_vencimiento=compra.fecha.date() + timedelta(days=30),
                            estado='pendiente'
                        )

                    messages.success(
                        request,
                        f"✅ Compra #{compra.numero_compra} registrada – Total: L{compra.total:.2f}"
                    )
                    return redirect('compras:resumen_compra', compra_id=compra.id)

            except Exception as e:
                messages.error(request, f"❌ Error al registrar la compra: {str(e)}")
        else:
            if not compra_form.is_valid():
                proveedor = compra_form.cleaned_data['proveedor']

            if proveedor.empresa != request.empresa:
                messages.error(request, "Proveedor inválido.")
                return redirect('compras:crear_compra')

                
            if not productos_validos:
                messages.error(request, "Debe agregar al menos un producto válido.")
    else:
        compra_form = CompraForm(empresa=request.empresa)
        # compra_form = CompraForm()  # ✅ siempre pasar empresa al form

    # ✅ productos solo de la empresa
    productos = Producto.objects.filter(activo=True, empresa=request.empresa).order_by('nombre')

    return render(request, 'compras/crear_compra.html', {
        'compra_form': compra_form,
        'productos': productos
    })


@login_required
@requiere_modulo('mod_compras')
@permission_required('compras.view_compra', raise_exception=True)
def resumen_compra(request, compra_id):
    compra = Compra.objects.get(id=compra_id, empresa=request.empresa)
    detalles = DetalleCompra.objects.filter(compra=compra, empresa=request.empresa)
    return render(request, 'compras/resumen_compra.html', {'compra': compra, 'detalles': detalles})

from django.core.paginator import Paginator

@login_required
@requiere_modulo('mod_compras')
@permission_required('compras.view_compras', raise_exception=True)
def resumen_compras(request):
    compras = Compra.objects.filter(empresa=request.empresa).order_by('-fecha')

    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    proveedor_id = request.GET.get('proveedor_id', '')
    proveedor_nombre = request.GET.get('proveedor_nombre', '')

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

    if proveedor_id:
        compras = compras.filter(proveedor_id=proveedor_id)

    total_general = compras.aggregate(Sum('total'))['total__sum'] or 0

    paginator = Paginator(compras, 2)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'compras/resumen_compras.html', {
        'page_obj': page_obj,
        'total_general': total_general,
        'f': {
            'desde': desde,
            'hasta': hasta,
            'proveedor_id': proveedor_id,
            'proveedor_nombre': proveedor_nombre,
        }
    })







   
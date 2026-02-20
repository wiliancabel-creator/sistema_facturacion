from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from cuentas.models import CuentaPorCobrar, CuentaPorPagar
from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from core.decorators import requiere_modulo
from django.db.models import Case, When, Value, IntegerField


@login_required
@requiere_modulo('mod_cuentas')
@permission_required('cuentas.view_cuentaporcobrar', raise_exception=True)
@permission_required('cuentas.view_cuentaporpagar', raise_exception=True)
def resumen_cuentas(request):
    estado = request.GET.get('estado', '')
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')

    cliente_id = request.GET.get('cliente_id', '')
    cliente_nombre = request.GET.get('cliente_nombre', '')

    proveedor_id = request.GET.get('proveedor_id', '')
    proveedor_nombre = request.GET.get('proveedor_nombre', '')

    # ✅ MULTI-TENANT: base filtrada por empresa
    por_cobrar = CuentaPorCobrar.objects.filter(empresa=request.empresa)
    por_pagar = CuentaPorPagar.objects.filter(empresa=request.empresa)

    if estado:
        por_cobrar = por_cobrar.filter(estado=estado)
        por_pagar = por_pagar.filter(estado=estado)

    if desde:
        try:
            f_desde = datetime.strptime(desde, "%Y-%m-%d").date()
            por_cobrar = por_cobrar.filter(venta__fecha__date__gte=f_desde)
            por_pagar = por_pagar.filter(compra__fecha__date__gte=f_desde)
        except ValueError:
            pass

    if hasta:
        try:
            f_hasta = datetime.strptime(hasta, "%Y-%m-%d").date()
            por_cobrar = por_cobrar.filter(venta__fecha__date__lte=f_hasta)
            por_pagar = por_pagar.filter(compra__fecha__date__lte=f_hasta)
        except ValueError:
            pass

    if cliente_id:
        por_cobrar = por_cobrar.filter(cliente_id=cliente_id)

    if proveedor_id:
        por_pagar = por_pagar.filter(proveedor_id=proveedor_id)

    # ✅ Orden: pendientes primero, luego pagados, más nuevos arriba
    por_cobrar = por_cobrar.annotate(
        orden_estado=Case(
            When(estado='pendiente', then=Value(0)),
            When(estado='pagado', then=Value(1)),
            default=Value(2),
            output_field=IntegerField()
        )
    ).order_by('orden_estado', '-venta__fecha', '-id')

    por_pagar = por_pagar.annotate(
        orden_estado=Case(
            When(estado='pendiente', then=Value(0)),
            When(estado='pagado', then=Value(1)),
            default=Value(2),
            output_field=IntegerField()
        )
    ).order_by('orden_estado', '-compra__fecha', '-id')

    return render(request, 'cuentas/resumen_cuentas.html', {
        'por_cobrar': por_cobrar,
        'por_pagar': por_pagar,
        'f': {
            'estado': estado,
            'desde': desde,
            'hasta': hasta,
            'cliente_id': cliente_id,
            'cliente_nombre': cliente_nombre,
            'proveedor_id': proveedor_id,
            'proveedor_nombre': proveedor_nombre,
        }
    })


@login_required
@requiere_modulo('mod_cuentas')
@permission_required('cuentas.change_cuentaporcobrar', raise_exception=True)
def registrar_pago_cliente(request, cuenta_id):
    # ✅ MULTI-TENANT: asegurar empresa
    cuenta = get_object_or_404(CuentaPorCobrar, id=cuenta_id, empresa=request.empresa)

    restante = cuenta.monto_pendiente - cuenta.monto_pagado

    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto') or '0')

        if monto <= 0:
            messages.error(request, "Ingrese un monto válido.")
            return render(request, 'cuentas/registrar_pago_cliente.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        if monto > restante:
            messages.error(request, f"No podés pagar más de L {restante:.2f}.")
            return render(request, 'cuentas/registrar_pago_cliente.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        cuenta.monto_pagado += monto
        cuenta.fecha_pago = timezone.now().date()

        if cuenta.monto_pagado >= cuenta.monto_pendiente:
            cuenta.estado = 'pagado'

        cuenta.save()
        return redirect('cuentas:resumen_cuentas')

    return render(request, 'cuentas/registrar_pago_cliente.html', {
        'cuenta': cuenta,
        'restante': restante
    })


@login_required
@requiere_modulo('mod_cuentas')
@permission_required('cuentas.change_cuentaporpagar', raise_exception=True)
def registrar_pago_proveedor(request, cuenta_id):
    # ✅ MULTI-TENANT: asegurar empresa
    cuenta = get_object_or_404(CuentaPorPagar, id=cuenta_id, empresa=request.empresa)

    restante = cuenta.monto_pendiente - cuenta.monto_pagado

    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto') or '0')

        if monto <= 0:
            messages.error(request, "Ingrese un monto válido.")
            return render(request, 'cuentas/registrar_pago_proveedor.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        if monto > restante:
            messages.error(request, f"No podés pagar más de L {restante:.2f}.")
            return render(request, 'cuentas/registrar_pago_proveedor.html', {
                'cuenta': cuenta,
                'restante': restante
            })

        cuenta.monto_pagado += monto
        cuenta.fecha_pago = timezone.now().date()

        if cuenta.monto_pagado >= cuenta.monto_pendiente:
            cuenta.estado = 'pagado'

        cuenta.save()
        return redirect('cuentas:resumen_cuentas')

    return render(request, 'cuentas/registrar_pago_proveedor.html', {
        'cuenta': cuenta,
        'restante': restante
    })

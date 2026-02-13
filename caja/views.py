from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.decorators import requiere_modulo

from caja.models import Caja, CajaSesion, CajaMovimiento


def _totales_pagos_por_metodo(desde_dt, hasta_dt):
    """
    Suma pagos por método en el rango de fechas usando relación venta__fecha.
    """
    from ventas.models import Pago  # importa aquí para evitar ciclos si fuera el caso

    qs = (Pago.objects  
          .filter(venta__fecha__gte=desde_dt, venta__fecha__lte=hasta_dt)
          .values('metodo')
          .annotate(total=Sum('monto')))

    tot = {'efectivo': Decimal('0.00'), 'tarjeta': Decimal('0.00'),
           'transferencia': Decimal('0.00'), 'otro': Decimal('0.00')}

    for row in qs:
        m = row['metodo']
        tot[m] = (row['total'] or Decimal('0.00'))
    return tot


@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.add_cajasesion', raise_exception=True)
def abrir_caja(request):
    caja = Caja.objects.filter(activa=True).first() or Caja.objects.create(nombre="Caja Principal", activa=True)

    # no permitir 2 sesiones abiertas para el mismo cajero (o para la misma caja, tú decides)
    sesion_abierta = CajaSesion.objects.filter(caja=caja, estado='abierta').first()
    if sesion_abierta:
        messages.warning(request, '⚠️ Ya hay una caja abierta.')
        return redirect('caja:panel_caja', sesion_id=sesion_abierta.id)

    if request.method == 'POST':
        monto = request.POST.get('monto_apertura', '0') or '0'
        try:
            monto = Decimal(monto)
        except:
            monto = Decimal('0.00')

        sesion = CajaSesion.objects.create(
            caja=caja,
            cajero=request.user,
            monto_apertura=monto
        )
        messages.success(request, '✅ Caja abierta correctamente.')
        return redirect('caja:panel_caja', sesion_id=sesion.id)

    return render(request, 'caja/abrir_caja.html', {'caja': caja})


@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.view_cajasesion', raise_exception=True)
def panel_caja(request, sesion_id):
    sesion = get_object_or_404(CajaSesion, id=sesion_id)
    if sesion.estado != 'abierta':
        return redirect('caja:detalle_cierre', sesion_id=sesion.id)

    # movimientos manuales
    if request.method == 'POST' and request.POST.get('accion') == 'movimiento':
        tipo = request.POST.get('tipo')
        concepto = request.POST.get('concepto', '').strip()
        monto = request.POST.get('monto', '0') or '0'

        try:
            monto = Decimal(monto)
        except:
            monto = Decimal('0.00')

        if monto <= 0 or tipo not in ['ingreso', 'egreso'] or not concepto:
            messages.error(request, '❌ Movimiento inválido.')
        else:
            CajaMovimiento.objects.create(
                sesion=sesion,
                tipo=tipo,
                concepto=concepto,
                monto=monto,
                usuario=request.user
            )
            messages.success(request, '✅ Movimiento registrado.')
        return redirect('caja:panel_caja', sesion_id=sesion.id)

    # totales actuales en vivo
    ahora = timezone.now()
    tot_pagos = _totales_pagos_por_metodo(sesion.fecha_apertura, ahora)

    ingresos = sesion.movimientos.filter(tipo='ingreso').aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    egresos = sesion.movimientos.filter(tipo='egreso').aggregate(s=Sum('monto'))['s'] or Decimal('0.00')

    efectivo_teorico = (sesion.monto_apertura + tot_pagos['efectivo'] + ingresos - egresos).quantize(Decimal('0.01'))

    context = {
        'sesion': sesion,
        'tot_pagos': tot_pagos,
        'ingresos': ingresos,
        'egresos': egresos,
        'efectivo_teorico': efectivo_teorico,
        'movimientos': sesion.movimientos.all().order_by('-fecha')[:30],
    }
    return render(request, 'caja/panel_caja.html', context)


@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.change_cajasesion', raise_exception=True)
def cerrar_caja(request, sesion_id):
    sesion = get_object_or_404(CajaSesion, id=sesion_id)

    if sesion.estado != 'abierta':
        return redirect('caja:detalle_cierre', sesion_id=sesion.id)

    ahora = timezone.now()
    tot_pagos = _totales_pagos_por_metodo(sesion.fecha_apertura, ahora)
    ingresos = sesion.movimientos.filter(tipo='ingreso').aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    egresos = sesion.movimientos.filter(tipo='egreso').aggregate(s=Sum('monto'))['s'] or Decimal('0.00')
    efectivo_teorico = (sesion.monto_apertura + tot_pagos['efectivo'] + ingresos - egresos).quantize(Decimal('0.01'))

    if request.method == 'POST':
        contado = request.POST.get('efectivo_contado', '0') or '0'
        observ = (request.POST.get('observacion', '') or '').strip()

        try:
            contado = Decimal(contado)
        except:
            contado = Decimal('0.00')

        diferencia = (contado - efectivo_teorico).quantize(Decimal('0.01'))

        if diferencia != 0 and not observ:
            messages.error(request, '❌ Debe escribir una observación si hay diferencia.')
            return redirect('caja:cerrar_caja', sesion_id=sesion.id)

        # snapshot
        sesion.total_efectivo = tot_pagos['efectivo']
        sesion.total_tarjeta = tot_pagos['tarjeta']
        sesion.total_transferencia = tot_pagos['transferencia']
        sesion.total_otro = tot_pagos['otro']
        sesion.ingresos_efectivo = ingresos
        sesion.egresos_efectivo = egresos
        sesion.efectivo_teorico = efectivo_teorico
        sesion.efectivo_contado = contado
        sesion.diferencia = diferencia
        sesion.observacion = observ
        sesion.fecha_cierre = ahora
        sesion.estado = 'cerrada'
        sesion.save()

        messages.success(request, '✅ Caja cerrada correctamente.')
        return redirect('caja:detalle_cierre', sesion_id=sesion.id)

    return render(request, 'caja/cerrar_caja.html', {
        'sesion': sesion,
        'tot_pagos': tot_pagos,
        'ingresos': ingresos,
        'egresos': egresos,
        'efectivo_teorico': efectivo_teorico,
    })


@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.view_cajasesion', raise_exception=True)
def detalle_cierre(request, sesion_id):
    sesion = get_object_or_404(CajaSesion, id=sesion_id)
    return render(request, 'caja/detalle_cierre.html', {'sesion': sesion})




@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.view_cajasesion', raise_exception=True)
def ticket_cierre(request, sesion_id):
    sesion = get_object_or_404(CajaSesion, id=sesion_id)
    return render(request, 'caja/ticket_cierre.html', {'sesion': sesion})


from django.db.models import Q

@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.view_cajasesion', raise_exception=True)  # si está en core: 'core.view_cajasesion'
def historial_cajas(request):
    q = (request.GET.get('q') or '').strip()
    estado = request.GET.get('estado') or ''
    desde = request.GET.get('desde') or ''
    hasta = request.GET.get('hasta') or ''

    sesiones = CajaSesion.objects.all().order_by('-fecha_apertura')

    if estado:
        sesiones = sesiones.filter(estado=estado)

    if desde:
        sesiones = sesiones.filter(fecha_apertura__date__gte=desde)

    if hasta:
        sesiones = sesiones.filter(fecha_apertura__date__lte=hasta)

    if q:
        sesiones = sesiones.filter(
            Q(cajero__username__icontains=q) |
            Q(cajero__first_name__icontains=q) |
            Q(cajero__last_name__icontains=q) |
            Q(caja__nombre__icontains=q)
        )

    return render(request, 'caja/historial_cajas.html', {
        'sesiones': sesiones,
        'f': {'q': q, 'estado': estado, 'desde': desde, 'hasta': hasta}
    })


@login_required
@requiere_modulo('mod_caja')
@permission_required('caja.view_cajasesion', raise_exception=True)  # si está en core: 'core.view_cajasesion'
def ver_cierre(request, sesion_id):
    sesion = get_object_or_404(CajaSesion, id=sesion_id)
    return render(request, 'caja/ver_cierre.html', {'sesion': sesion})
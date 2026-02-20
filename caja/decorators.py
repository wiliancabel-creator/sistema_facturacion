from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone

from caja.models import CajaSesion  # si tus modelos siguen en core, cambia a: from core.models import CajaSesion


def requiere_caja_abierta(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):

        # ✅ FILTRAR POR EMPRESA
        sesion = CajaSesion.objects.filter(
            empresa=request.empresa,
            estado='abierta'
        ).order_by('-fecha_apertura').first()

        if not sesion:
            messages.error(request, "❌ No puedes operar: no hay una caja abierta en tu sistema.")
            return redirect('caja:abrir_caja')

        # (Opcional) validar mismo cajero
        # if sesion.cajero_id != request.user.id:
        #     messages.error(request, "❌ Hay una caja abierta, pero pertenece a otro cajero.")
        #     return redirect('caja:panel_caja', sesion_id=sesion.id)

        return view_func(request, *args, **kwargs)

    return _wrapped


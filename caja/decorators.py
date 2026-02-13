from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone

from caja.models import CajaSesion  # si tus modelos siguen en core, cambia a: from core.models import CajaSesion


def requiere_caja_abierta(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        sesion = CajaSesion.objects.filter(estado='abierta').order_by('-fecha_apertura').first()

        if not sesion:
            messages.error(request, "❌ No puedes operar: no hay una caja abierta. Abre caja primero.")
            return redirect('caja:abrir_caja')

        # (Opcional) Si quieres que solo el mismo cajero pueda usar su caja:
        # if sesion.cajero_id != request.user.id:
        #     messages.error(request, "❌ Hay una caja abierta, pero pertenece a otro cajero.")
        #     return redirect('caja:panel_caja', sesion_id=sesion.id)

        return view_func(request, *args, **kwargs)
    return _wrapped

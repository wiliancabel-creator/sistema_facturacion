from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from configuracion.models import ModuloConfig

def requiere_modulo(nombre_modulo):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            mod = ModuloConfig.objects.first()
            if not mod:
                mod = ModuloConfig.objects.create()

            if not getattr(mod, nombre_modulo, False):
                messages.error(request, "Este módulo no está activo en tu plan.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from configuracion.models import ModuloConfig

def requiere_modulo(nombre_modulo):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):

            # ✅ multi-tenant: módulos por empresa
            mod, _ = ModuloConfig.objects.get_or_create(empresa=request.empresa)

            if not getattr(mod, nombre_modulo, False):
                messages.error(request, "Este módulo no está activo en tu plan.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator



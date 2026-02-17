from django.shortcuts import redirect
from django.urls import reverse

class CurrentEmpresaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            request.empresa = getattr(user, "empresa", None)

            # ✅ Si está logueado pero no tiene empresa, lo mandamos a login
            # (o podrías mostrar un mensaje, pero esto evita errores en módulos)
            if request.empresa is None and request.path not in [reverse('logout'), reverse('login')]:
                return redirect('logout')

        return self.get_response(request)

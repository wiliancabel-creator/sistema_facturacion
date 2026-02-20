from core.models import Empresa

class CurrentEmpresaMiddleware:
    """
    - Usuario normal: usa request.user.empresa
    - Superuser: si hay empresa_id en sesión, usa esa (para poder "cambiar empresa")
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None

        if request.user.is_authenticated:
            # 1) Superuser: empresa seleccionada en sesión
            if request.user.is_superuser:
                empresa_id = request.session.get("empresa_id")
                if empresa_id:
                    request.empresa = Empresa.objects.filter(id=empresa_id).first()

            # 2) Usuario normal: empresa del usuario
            if request.empresa is None:
                request.empresa = getattr(request.user, "empresa", None)

        return self.get_response(request)



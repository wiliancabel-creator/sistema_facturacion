class CurrentEmpresaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.empresa = None
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            request.empresa = getattr(user, "empresa", None)

        return self.get_response(request)

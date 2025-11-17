from .models import EmpresaConfig

def empresa_context(request):
    try:
        empresa = EmpresaConfig.objects.get(pk=1)
    except EmpresaConfig.DoesNotExist:
        empresa = None

    return {
        'empresa': empresa
    }

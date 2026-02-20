from configuracion.models import EmpresaConfig, ModuloConfig

def empresa_config(request):
    # En /login/ no hay empresa seleccionada -> no crear nada
    empresa = getattr(request, "empresa", None)
    if not empresa:
        return {"empresa": None}

    config, _ = EmpresaConfig.objects.get_or_create(
        empresa=empresa,
        defaults={
            "nombre": empresa.nombre,
            "rtn": "00000000000000",
            "direccion": "Pendiente",
        }
    )
    return {"empresa": config}


def modulos_config(request):
    empresa = getattr(request, "empresa", None)
    if not empresa:
        return {"modulos": None}

    modulos, _ = ModuloConfig.objects.get_or_create(empresa=empresa)
    return {"modulos": modulos}




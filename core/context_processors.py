from configuracion.models import EmpresaConfig

def empresa_config(request):
    empresa = EmpresaConfig.objects.first()
    if not empresa:
        empresa = EmpresaConfig.objects.create(
            nombre="Mi Empresa",
            rtn="",
            direccion="",
        )
    return {"empresa": empresa}


from configuracion.models import ModuloConfig

def modulos_config(request):
    modulos = ModuloConfig.objects.first()
    if not modulos:
        modulos = ModuloConfig.objects.create()
    return {"modulos": modulos}

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from configuracion.models import EmpresaConfig
from configuracion.forms import EmpresaConfigForm

@login_required
@permission_required('configuracion.change_empresaconfig', raise_exception=True)
def configuracion_empresa(request):
    # ✅ obtenemos/creamos la config de ESTA empresa
    config, _ = EmpresaConfig.objects.get_or_create(
        empresa=request.empresa,
        defaults={
            "nombre": request.empresa.nombre if hasattr(request.empresa, "nombre") else "",
            "rtn": "",
            "direccion": "",
        }
    )

    if request.method == 'POST':
        form = EmpresaConfigForm(request.POST, instance=config)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.empresa  # ✅ seguridad extra
            obj.save()
            messages.success(request, "Configuración guardada correctamente.")
            return redirect('configuracion_empresa')
    else:
        form = EmpresaConfigForm(instance=config)

    return render(request, 'configuracion/configuracion_empresa.html', {'form': form})


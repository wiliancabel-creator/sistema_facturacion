
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from configuracion.models import EmpresaConfig
from configuracion.forms import EmpresaConfigForm




@login_required
@permission_required('configuracion.change_empresaconfig')
def configuracion_empresa(request):
    try:
        config = EmpresaConfig.objects.get(pk=1)
    except EmpresaConfig.DoesNotExist:
        config = EmpresaConfig(pk=1)

    if request.method == 'POST':
        form = EmpresaConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración guardada correctamente.")
            return redirect('configuracion_empresa')
    else:
        form = EmpresaConfigForm(instance=config)

    return render(request, 'configuracion/configuracion_empresa.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from core.decorators import requiere_modulo
from cai.models import Cai
from cai.forms import CaiForm

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.view_cai', raise_exception=True)
def listar_cai(request):
    cais = Cai.objects.filter(empresa=request.empresa).order_by('-activo', 'fecha_limite')
    return render(request, 'cai/listar_cai.html', {'cais': cais})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.add_cai', raise_exception=True)
def crear_cai(request):
    form = CaiForm(request.POST or None)
    if form.is_valid():
        cai = form.save(commit=False)
        cai.empresa = request.empresa  # ✅ MULTI-TENANT
        cai.save()
        return redirect('cai:listar_cai')
    return render(request, 'cai/crear_cai.html', {'form': form})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.change_cai', raise_exception=True)
def editar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk, empresa=request.empresa)  # ✅ MULTI-TENANT
    form = CaiForm(request.POST or None, instance=cai)
    if form.is_valid():
        form.save()
        return redirect('cai:listar_cai')
    return render(request, 'cai/editar_cai.html', {'form': form})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.delete_cai', raise_exception=True)
def eliminar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk, empresa=request.empresa)  # ✅ MULTI-TENANT
    cai.delete()
    return redirect('cai:listar_cai')


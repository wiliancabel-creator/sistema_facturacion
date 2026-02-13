
from django.shortcuts import render, redirect, get_object_or_404

from cai.models import Cai

from cai.forms import CaiForm

from django.contrib.auth.decorators import login_required, permission_required

from core.decorators import requiere_modulo

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.view_cai')
def listar_cai(request):
    cais = Cai.objects.all().order_by('-activo', 'fecha_limite')
    return render(request, 'cai/listar_cai.html', {'cais': cais})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.add_cai')
def crear_cai(request):
    form = CaiForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('cai:listar_cai')
    return render(request, 'cai/crear_cai.html', {'form': form})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.change_cai')
def editar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk)
    form = CaiForm(request.POST or None, instance=cai)
    if form.is_valid():
        form.save()
        return redirect('cai:listar_cai')
    return render(request, 'cai/editar_cai.html', {'form': form})

@login_required
@requiere_modulo('mod_cai')
@permission_required('cai.delete_cai')
def eliminar_cai(request, pk):
    cai = get_object_or_404(Cai, pk=pk)
    cai.delete()
    return redirect('cai:listar_cai')

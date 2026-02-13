
from django.shortcuts import render, redirect

from clientes.models import Cliente
from clientes.forms import ClienteForm

from django.contrib.auth.decorators import login_required, permission_required

from django.http import JsonResponse


@login_required

@permission_required('clientes.view_cliente', raise_exception=True)
def listar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/listar_clientes.html', {'clientes': clientes})

@login_required

@permission_required('clientes.add_cliente', raise_exception=True)
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes:listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})


@login_required

def buscar_clientes(request):
    term = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nombre__icontains=term).values('id', 'nombre')[:20]
    results = [
        {"id": c["id"], "text": f"{c['id']} - {c['nombre']}"}
        for c in clientes
    ]
    return JsonResponse({"results": results})


from django.shortcuts import render, redirect

from clientes.models import Cliente
from clientes.forms import ClienteForm

from django.contrib.auth.decorators import login_required, permission_required

from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from core.decorators import requiere_modulo

@login_required
@requiere_modulo('mod_clientes')
@permission_required('clientes.view_cliente', raise_exception=True)
def listar_clientes(request):
    q = (request.GET.get('q') or '').strip()

    clientes_qs = Cliente.objects.all().order_by('-id')

    # ✅ FILTRO (busca en TODOS, no solo la página)
    if q:
        clientes_qs = clientes_qs.filter(
            Q(nombre__icontains=q) |
            Q(telefono__icontains=q) |
            Q(correo__icontains=q) |
            Q(rtn__icontains=q)   # si tu modelo tiene rtn
        )

    paginator = Paginator(clientes_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'clientes/listar_clientes.html', {
        'page_obj': page_obj,
        'clientes': page_obj.object_list,
        'q': q,
    })


@login_required
@requiere_modulo('mod_clientes')
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
@requiere_modulo('mod_clientes')
def buscar_clientes(request):
    term = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nombre__icontains=term).values('id', 'nombre')[:20]
    results = [
        {"id": c["id"], "text": f"{c['id']} - {c['nombre']}"}
        for c in clientes
    ]
    return JsonResponse({"results": results})

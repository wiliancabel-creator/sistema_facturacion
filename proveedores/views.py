
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory


from proveedores.forms import ProveedorForm
from proveedores.models import Proveedor

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse


@login_required
@permission_required('proveedores.add_proveedor', raise_exception=True)
def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('proveedores:lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/registrar.html', {'form': form})

@login_required
@permission_required('proveedores.view_proveedor', raise_exception=True)
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/lista.html', {'proveedores': proveedores})


@login_required
def buscar_proveedor(request):
    """
    Busca proveedor por ID, RTN, nombre parcial, teléfono o correo.
    Devuelve JSON para autocompletar formularios.
    """
    q = request.GET.get('q', '').strip()

    if not q:
        return JsonResponse({'encontrado': False, 'error': 'Campo vacío'})

    proveedor = None

    try:
        # 1. Buscar por ID numérico
        if q.isdigit():
            proveedor = Proveedor.objects.filter(id=int(q), activo=True).first()

        # 2. Buscar por RTN exacto
        if not proveedor:
            proveedor = Proveedor.objects.filter(rtn=q, activo=True).first()

        # 3. Buscar por teléfono
        if not proveedor:
            proveedor = Proveedor.objects.filter(telefono__icontains=q, activo=True).first()

        # 4. Buscar por correo
        if not proveedor:
            proveedor = Proveedor.objects.filter(correo__icontains=q, activo=True).first()

        # 5. Buscar por nombre parcial
        if not proveedor:
            proveedor = Proveedor.objects.filter(nombre__icontains=q, activo=True).first()

        if proveedor:
            return JsonResponse({
                'encontrado': True,
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'rtn': proveedor.rtn or '',
                'telefono': proveedor.telefono or '',
                'correo': proveedor.correo or '',
                'direccion': proveedor.direccion or '',
                'contacto': proveedor.contacto or '',
            })

        return JsonResponse({'encontrado': False, 'error': "Proveedor no encontrado"})

    except Exception as e:
        return JsonResponse({'encontrado': False, 'error': f'Error: {str(e)}'})

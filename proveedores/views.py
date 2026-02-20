
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory


from proveedores.forms import ProveedorForm
from proveedores.models import Proveedor

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.core.paginator import Paginator

@login_required
@permission_required('proveedores.add_proveedor', raise_exception=True)
def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            prov = form.save(commit=False)
            prov.empresa = request.empresa  # ✅ MULTI-TENANT
            prov.save()
            return redirect('proveedores:lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/registrar.html', {'form': form})


@login_required
@permission_required('proveedores.view_proveedor', raise_exception=True)
def lista_proveedores(request):
    proveedores = Proveedor.objects.filter(empresa=request.empresa).order_by('nombre')
    
    paginator = Paginator(proveedores, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'proveedores/lista.html', {'page_obj': page_obj})



@login_required
def buscar_proveedor(request):
    q = request.GET.get('q', '').strip()

    if not q:
        return JsonResponse({'encontrado': False, 'error': 'Campo vacío'})

    proveedor = None

    try:
        base = Proveedor.objects.filter(activo=True, empresa=request.empresa)

        if q.isdigit():
            proveedor = base.filter(id=int(q)).first()

        if not proveedor:
            proveedor = base.filter(rtn=q).first()

        if not proveedor:
            proveedor = base.filter(telefono__icontains=q).first()

        if not proveedor:
            proveedor = base.filter(correo__icontains=q).first()

        if not proveedor:
            proveedor = base.filter(nombre__icontains=q).first()

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


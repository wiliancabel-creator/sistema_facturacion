from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator

from core.decorators import requiere_modulo
from productos.models import Producto, Categoria
from productos.forms import ProductoForm, CategoriaForm


@login_required
@requiere_modulo('mod_productos')
@permission_required('productos.view_producto', raise_exception=True)
def listar_productos(request):
    query = (request.GET.get('q') or '').strip()
    categoria_id = (request.GET.get('categoria') or '').strip()

    # 🔒 SOLO productos de la empresa actual
    productos = Producto.objects.filter(empresa=request.empresa)

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(codigo__icontains=query) |
            Q(codigo_barra__icontains=query)
        )

    if categoria_id.isdigit():
        # 🔒 validar que la categoría sea de la misma empresa
        productos = productos.filter(categoria_id=categoria_id, categoria__empresa=request.empresa)

    productos = productos.order_by('-id')

    paginator = Paginator(productos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🔒 SOLO categorías de la empresa actual
    categorias = Categoria.objects.filter(empresa=request.empresa).order_by('nombre')

    return render(request, 'productos/listar_productos.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'categoria_seleccionada': categoria_id,
        'query': query
    })


@login_required
@requiere_modulo('mod_productos')
@permission_required('productos.add_producto', raise_exception=True)
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = request.empresa  # 🔒 asignar empresa
            producto.save()
            messages.success(request, "✅ Producto creado correctamente.")
            return redirect('productos:listar_productos')
    else:
        form = ProductoForm()

    return render(request, 'productos/agregar_producto.html', {'form': form})


@login_required
@requiere_modulo('mod_productos')
@permission_required('productos.change_producto', raise_exception=True)
def editar_producto(request, pk):
    # 🔒 no permitir editar productos de otra empresa
    producto = get_object_or_404(Producto, pk=pk, empresa=request.empresa)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Producto '{producto.nombre}' actualizado correctamente.")
            return redirect('productos:listar_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'productos/editar_producto.html', {
        'form': form,
        'producto': producto
    })


@login_required
@requiere_modulo('mod_productos')
@permission_required('productos.delete_producto', raise_exception=True)
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, empresa=request.empresa)

    if request.method == 'POST':
        producto.delete()
        messages.success(request, f"🗑 Producto '{producto.nombre}' eliminado correctamente.")
        return redirect('productos:listar_productos')

    return render(request, 'productos/eliminar_producto.html', {
        'producto': producto
    })


@login_required
@requiere_modulo('mod_productos')
@permission_required('productos.add_categoria', raise_exception=True)
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.empresa = request.empresa  # 🔒 asignar empresa
            categoria.save()
            messages.success(request, '✅ Categoría creada correctamente.')
            return redirect('productos:listar_productos')
    else:
        form = CategoriaForm()

    return render(request, 'productos/crear_categoria.html', {'form': form})



from django.shortcuts import render, redirect

from django.db.models.functions import TruncDay, TruncMonth, ExtractYear
from django.core.serializers.json import DjangoJSONEncoder
import json

from productos.models import Producto

from ventas.models import Venta,DetalleVenta

from compras.models import Compra,DetalleCompra
from proveedores.models import Proveedor

from django.utils import timezone
from django.db.models import Sum, Q, Max
from clientes.models import Cliente

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login
from django.http import JsonResponse





@login_required
def dashboard(request):
    hoy = timezone.localdate()

    ventas_hoy = Venta.objects.filter(empresa=request.empresa,fecha__date=hoy).aggregate(total=Sum('total'))['total'] or 0
    compras_hoy = Compra.objects.filter(empresa=request.empresa,fecha__date=hoy).aggregate(total=Sum('total'))['total'] or 0

    productos_vendidos_hoy = DetalleVenta.objects.filter(venta__empresa=request.empresa, venta__fecha__date=hoy).aggregate(cantidad=Sum('cantidad'))['cantidad'] or 0
    productos_comprados_hoy = DetalleCompra.objects.filter(compra__empresa=request.empresa, compra__fecha__date=hoy).aggregate(cantidad=Sum('cantidad'))['cantidad'] or 0

    total_ventas = Venta.objects.filter(empresa=request.empresa).aggregate(total=Sum('total'))['total'] or 0
    total_compras = Compra.objects.filter(empresa=request.empresa).aggregate(total=Sum('total'))['total'] or 0

    total_productos = Producto.objects.filter(empresa=request.empresa).count()
    total_clientes = Cliente.objects.filter(empresa=request.empresa).count()
    total_proveedores = Proveedor.objects.filter(empresa=request.empresa).count()

    context = {
        'ventas_hoy': ventas_hoy,
        'compras_hoy': compras_hoy,
        'productos_vendidos_hoy': productos_vendidos_hoy,
        'productos_comprados_hoy': productos_comprados_hoy,
        'total_ventas': total_ventas,
        'total_compras': total_compras,
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
    }

    return render(request, "dashboard/dashboard.html", context)




@login_required
@permission_required('core.view_venta', raise_exception=True)
def dashboard_graficos(request):
    # Ventas por día (últimos 30 días)
    ventas_diarias = (
        Venta.objects.annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('total'))
        .order_by('dia')
    )

    compras_diarias = (
        Compra.objects.annotate(dia=TruncDay('fecha'))
        .values('dia')
        .annotate(total=Sum('total'))
        .order_by('dia')
    )

    # Ventas y compras por mes
    ventas_mensuales = (
        Venta.objects.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    compras_mensuales = (
        Compra.objects.annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('total'))
        .order_by('mes')
    )

    # Ventas y compras por año
    ventas_anuales = (
        Venta.objects.annotate(año=ExtractYear('fecha'))
        .values('año')
        .annotate(total=Sum('total'))
        .order_by('año')
    )

    compras_anuales = (
        Compra.objects.annotate(año=ExtractYear('fecha'))
        .values('año')
        .annotate(total=Sum('total'))
        .order_by('año')
    )

    context = {
        'ventas_diarias': json.dumps(list(ventas_diarias), cls=DjangoJSONEncoder),
        'compras_diarias': json.dumps(list(compras_diarias), cls=DjangoJSONEncoder),
        'ventas_mensuales': json.dumps(list(ventas_mensuales), cls=DjangoJSONEncoder),
        'compras_mensuales': json.dumps(list(compras_mensuales), cls=DjangoJSONEncoder),
        'ventas_anuales': json.dumps(list(ventas_anuales), cls=DjangoJSONEncoder),
        'compras_anuales': json.dumps(list(compras_anuales), cls=DjangoJSONEncoder),
    }

    return render(request, 'dashboard/dashboard_graficos.html', context)





def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username} 👋')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'auth/login.html')
    
from django.shortcuts import redirect, get_object_or_404
from core.models import Empresa

@login_required
def seleccionar_empresa(request, empresa_id):
    if not request.user.is_superuser:
        return redirect("dashboard")

    empresa = get_object_or_404(Empresa, id=empresa_id)
    request.session["empresa_id"] = empresa.id
    return redirect("dashboard")




from productos.forms import ProductoForm
from proveedores.forms import ProveedorForm

@login_required
def crear_producto_ajax(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = request.empresa  # ✅ MULTI-TENANT
            producto.save()
            return JsonResponse({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'codigo': producto.codigo,
                    'nombre': producto.nombre,
                    'precio': str(producto.precio),
                    'tipo_impuesto': producto.tipo_impuesto,
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})



@login_required
def crear_proveedor_ajax(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.empresa = request.empresa  # ✅ MULTI-TENANT
            proveedor.save()
            return JsonResponse({
                'success': True,
                'proveedor': {
                    'id': proveedor.id,
                    'nombre': proveedor.nombre,
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def crear_cliente_ajax(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        rtn = request.POST.get('rtn', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio'})

        try:
            cliente = Cliente.objects.create(
                empresa=request.empresa,   # ✅ MULTI-TENANT
                nombre=nombre,
                rtn=rtn if rtn else None,
                telefono=telefono if telefono else None,
                direccion=direccion if direccion else None
            )
            return JsonResponse({'success': True, 'cliente': {'id': cliente.id, 'nombre': cliente.nombre}})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})




@login_required
def sugerencias_proveedores(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'proveedores': []})

    try:
        proveedores = Proveedor.objects.filter(
            empresa=request.empresa,   # ✅ MULTI-TENANT
            activo=True,
            nombre__icontains=query
        )[:10]

        resultados = [{
            'id': p.id,
            'nombre': p.nombre,
            'rtn': p.rtn or '',
        } for p in proveedores]

        return JsonResponse({'proveedores': resultados})

    except Exception as e:
        return JsonResponse({'proveedores': [], 'error': str(e)})




from .models import Empresa
from django.db.models import Q

@login_required
def sugerencias_productos(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'productos': []})

    try:
        productos = Producto.objects.filter(
            empresa=request.empresa,   # ✅ MULTI-TENANT
            activo=True
        ).filter(
            Q(codigo__icontains=query) |
            Q(codigo_barra__icontains=query) |
            Q(nombre__icontains=query)
        )[:10]

        resultados = [{
            'id': p.id,
            'codigo': p.codigo,
            'codigo_barra': p.codigo_barra or '',
            'nombre': p.nombre,
            'precio': str(p.precio),
            'stock': p.stock,
            'tipo_impuesto': p.tipo_impuesto,
            'display': f"{p.codigo} - {p.nombre} (Stock: {p.stock})"
        } for p in productos]

        return JsonResponse({'productos': resultados})

    except Exception as e:
        return JsonResponse({'productos': [], 'error': str(e)})





@login_required
def sugerencias_clientes(request):
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'clientes': []})

    try:
        clientes = Cliente.objects.filter(
            empresa=request.empresa,   # ✅ MULTI-TENANT
        ).filter(
            Q(nombre__icontains=query) |
            Q(rtn__icontains=query) |
            Q(telefono__icontains=query)
        )[:10]

        resultados = [{
            'id': c.id,
            'nombre': c.nombre,
            'rtn': c.rtn or '',
            'telefono': c.telefono or '',
        } for c in clientes]

        return JsonResponse({'clientes': resultados})

    except Exception as e:
        return JsonResponse({'clientes': [], 'error': str(e)})

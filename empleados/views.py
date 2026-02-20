
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.auth.decorators import login_required


from empleados.models import Empleado, PagoEmpleado
from empleados.forms import EmpleadoForm, PagoEmpleadoForm
from core.decorators import requiere_modulo
from django.core.paginator import Paginator

# Listado de empleados
@login_required
@requiere_modulo('mod_empleados')
def lista_empleados(request):
    empleados = Empleado.objects.filter(empresa=request.empresa).order_by('nombre')
    paginator = Paginator(empleados, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, "empleados/lista_empleados.html", {"page_obj": page_obj})


# Crear emplead
@login_required
@requiere_modulo('mod_empleados')
def crear_empleado(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.empresa = request.empresa
            emp.save()
            messages.success(request, "Empleado registrado correctamente")
            return redirect("empleados:lista_empleados")
    else:
        form = EmpleadoForm()
    return render(request, "empleados/empleado_form.html", {"form": form})


# Editar empleado
@login_required
@requiere_modulo('mod_empleados')
def editar_empleado(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk, empresa=request.empresa)
    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            emp = form.save(commit=False)
            emp.empresa = request.empresa  # seguridad extra
            emp.save()
            messages.success(request, "Empleado actualizado correctamente")
            return redirect("empleados:lista_empleados")
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, "empleados/empleado_form.html", {"form": form})


# Create your views here.
# Registrar pago
@login_required
@requiere_modulo('mod_empleados')
def registrar_pago(request):
    if request.method == "POST":
        form = PagoEmpleadoForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            pago = form.save(commit=False)

            # ✅ seguridad: empleado debe ser de la empresa
            if pago.empleado.empresa_id != request.empresa.id:
                messages.error(request, "Empleado inválido.")
                return redirect("empleados:registrar_pago")

            pago.empresa = request.empresa
            pago.save()
            messages.success(request, "Pago registrado correctamente")
            return redirect("empleados:lista_pagos")
    else:
        form = PagoEmpleadoForm(empresa=request.empresa)

    salarios = {
        e.id: float(e.salario_base)
        for e in Empleado.objects.filter(empresa=request.empresa)
    }

    return render(request, "empleados/pago_form.html", {
        "form": form,
        "salarios": salarios
    })



# Listado de pagos
@login_required
@requiere_modulo('mod_empleados')
def lista_pagos(request):
    pagos = PagoEmpleado.objects.select_related("empleado").filter(
        empresa=request.empresa
    ).order_by("-fecha_pago")
    
    paginator = Paginator(pagos, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "empleados/lista_pagos.html", {"page_obj": page_obj})


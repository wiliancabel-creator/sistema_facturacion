
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.auth.decorators import login_required


from empleados.models import Empleado, PagoEmpleado
from empleados.forms import EmpleadoForm, PagoEmpleadoForm
from core.decorators import requiere_modulo

# Listado de empleados
@login_required
@requiere_modulo('mod_empleados')
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, "empleados/lista_empleados.html", {"empleados": empleados})

# Crear emplead
@login_required
@requiere_modulo('mod_empleados')
def crear_empleado(request):
    if request.method == "POST":
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado registrado correctamente")
            return redirect("empleados:lista_empleados")
    else:
        form = EmpleadoForm()
    return render(request, "empleados/empleado_form.html", {"form": form})

# Editar empleado
@login_required
@requiere_modulo('mod_empleados')
def editar_empleado(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == "POST":
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
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
        form = PagoEmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago registrado correctamente")
            return redirect("empleados:lista_pagos")
    else:
        form = PagoEmpleadoForm()

    # 👇 Diccionario {id_empleado: salario_base}
    salarios = {e.id: float(e.salario_base) for e in Empleado.objects.all()}

    return render(request, "empleados/pago_form.html", {
        "form": form,
        "salarios": salarios
    })


# Listado de pagos
@login_required
@requiere_modulo('mod_empleados')
def lista_pagos(request):
    pagos = PagoEmpleado.objects.select_related("empleado").order_by("-fecha_pago")
    return render(request, "empleados/lista_pagos.html", {"pagos": pagos})

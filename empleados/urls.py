from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = "empleados"

urlpatterns = [
 # Empleados y Pagos
    path("", views.lista_empleados, name="lista_empleados"),
    path("nuevo/", views.crear_empleado, name="crear_empleado"),
    path("<int:pk>/editar/", views.editar_empleado, name="editar_empleado"),
    path("pagos/", views.lista_pagos, name="lista_pagos"),
    path("pagos/nuevo/", views.registrar_pago, name="registrar_pago"),

]
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "proveedores"

urlpatterns = [
# Proveedores
    path('', views.lista_proveedores, name='lista_proveedores'),
    path('registrar/', views.registrar_proveedor, name='registrar_proveedor'),
    path("buscar/", views.buscar_proveedor, name="buscar_proveedor"),

]
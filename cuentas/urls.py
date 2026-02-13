from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "cuentas"

urlpatterns = [
# Cuentas
    path('', views.resumen_cuentas, name='resumen_cuentas'),
    path('cobrar/<int:cuenta_id>/', views.registrar_pago_cliente, name='registrar_pago_cliente'),
    path('pagar/<int:cuenta_id>/', views.registrar_pago_proveedor, name='registrar_pago_proveedor'),
    
]
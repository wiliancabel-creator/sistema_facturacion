from django.urls import path
from .import views

app_name = "ventas"

urlpatterns = [
    path('', views.resumen_ventas, name='resumen_ventas'),          # /ventas/
    path('crear/', views.crear_venta, name='crear_venta'),          # /ventas/crear/
    path('buscar-producto/', views.buscar_producto, name='buscar_producto'),
    path('buscar-producto-id/', views.buscar_producto_id, name='buscar_producto_id'),
    path('factura/<int:venta_id>/', views.factura, name='factura'),
]

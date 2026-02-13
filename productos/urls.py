from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "productos"

urlpatterns = [
# Productos
path('', views.listar_productos, name='listar_productos'),
path('agregar/', views.agregar_producto, name='agregar_producto'),
path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),

]
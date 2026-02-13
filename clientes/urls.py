from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "clientes"

urlpatterns = [
# Clientes
    path('', views.listar_clientes, name='listar_clientes'),
    path('crear/', views.crear_cliente, name='crear_cliente'),
    path('buscar/', views.buscar_clientes, name='buscar_clientes'),

]
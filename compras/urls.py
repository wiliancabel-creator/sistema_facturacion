from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "compras"

urlpatterns = [
# Compras
    path('crear', views.crear_compra, name='crear_compra'),
    path('resumen/', views.resumen_compras, name='resumen_compras'),
    path('<int:compra_id>/', views.resumen_compra, name='resumen_compra'),


]
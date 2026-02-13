from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "cai"

urlpatterns = [
# CAI
    path('', views.listar_cai, name='listar_cai'),
    path('crear/', views.crear_cai, name='crear_cai'),
    path('editar/<int:pk>/', views.editar_cai, name='editar_cai'),
    path('eliminar/<int:pk>/', views.eliminar_cai, name='eliminar_cai'),

]
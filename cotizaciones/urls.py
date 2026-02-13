from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "cotizaciones"

urlpatterns = [
# Cotizaciones
    path('', views.lista_cotizaciones, name='lista_cotizaciones'),
    path('nueva/', views.crear_cotizacion, name='crear_cotizacion'),
    path('<int:cotizacion_id>/', views.detalle_cotizacion, name='detalle_cotizacion'),
    path('<int:cotizacion_id>/facturar/', views.facturar_cotizacion, name='facturar_cotizacion'),
    path('<int:cotizacion_id>/editar/', views.editar_cotizacion, name='editar_cotizacion'),
    path('<int:cotizacion_id>/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),

]
from django.urls import path
from . import views

app_name = "caja"

urlpatterns = [
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('panel/<int:sesion_id>/', views.panel_caja, name='panel_caja'),
    path('cerrar/<int:sesion_id>/', views.cerrar_caja, name='cerrar_caja'),
    path('detalle/<int:sesion_id>/', views.detalle_cierre, name='detalle_cierre'),
    path('ticket/<int:sesion_id>/', views.ticket_cierre, name='ticket_cierre'),
    path('historial/', views.historial_cajas, name='historial_cajas'),
    path('cierre/<int:sesion_id>/', views.ver_cierre, name='ver_cierre'),


]

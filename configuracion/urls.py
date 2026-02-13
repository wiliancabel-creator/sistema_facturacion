from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "configuracion"

urlpatterns = [
    # EMPRESA
    path('Empresa', views.configuracion_empresa, name='configuracion_empresa'),

]
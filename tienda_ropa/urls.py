
# tienda_ropa/urls.py - URL PRINCIPAL CORREGIDA
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Solo esta línea para core
]

# tienda_ropa/urls.py - URL PRINCIPAL CORREGIDA
from django.contrib import admin
from django.urls import path, include

from sistema_base import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Solo esta línea para core
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
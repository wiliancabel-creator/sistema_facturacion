from django.contrib import admin
from .models import (
    Categoria, Producto, Venta, DetalleVenta,
    Compra, DetalleCompra, Cliente,
    CuentaPorCobrar, CuentaPorPagar, Usuario,Cotizacion, Empleado,
    Cai  # ← Importar el modelo Cai
)

# Registración estándar de otros modelos
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Compra)
admin.site.register(DetalleCompra)
admin.site.register(Cliente)
admin.site.register(CuentaPorCobrar)
admin.site.register(CuentaPorPagar)
admin.site.register(Usuario)
admin.site.register(Cotizacion)
admin.site.register(Empleado)

# Registrar el modelo Cai con su ModelAdmin
@admin.register(Cai)
class CaiAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'correlativo_actual', 'rango_final', 'fecha_limite', 'activo')
    list_filter  = ('activo',)
    ordering     = ('-fecha_limite',)
    search_fields = ('codigo',)       # Ejemplo: buscar por código
    list_editable = ('activo',)       # Ejemplo: activar/desactivar desde la lista

from django.contrib import admin
from clientes.models import Cliente
from compras.models import Compra, DetalleCompra
from cuentas.models import CuentaPorCobrar, CuentaPorPagar
from productos.models import Categoria, Producto
from ventas.models import Venta, DetalleVenta
from cai.models import Cai                             
from core.models import Usuario
from cotizaciones.models import Cotizacion
from empleados.models import Empleado

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

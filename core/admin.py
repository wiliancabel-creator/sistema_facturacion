from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

from clientes.models import Cliente
from compras.models import Compra, DetalleCompra
from cuentas.models import CuentaPorCobrar, CuentaPorPagar
from productos.models import Categoria, Producto
from ventas.models import Venta, DetalleVenta
from cai.models import Cai
from core.models import Empresa
from cotizaciones.models import Cotizacion
from empleados.models import Empleado


# ===========================
#   REGISTROS NORMALES
# ===========================
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Compra)
admin.site.register(DetalleCompra)
admin.site.register(Cliente)
admin.site.register(CuentaPorCobrar)
admin.site.register(CuentaPorPagar)
admin.site.register(Cotizacion)
admin.site.register(Empleado)
admin.site.register(Empresa)


# ===========================
#   CAI ADMIN
# ===========================
@admin.register(Cai)
class CaiAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'correlativo_actual', 'rango_final', 'fecha_limite', 'activo')
    list_filter = ('activo',)
    ordering = ('-fecha_limite',)
    search_fields = ('codigo',)
    list_editable = ('activo',)


# ===========================
#   USUARIO ADMIN (IMPORTANTE)
# ===========================
Usuario = get_user_model()

class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "email", "empresa")

class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = (
            "username", "email", "empresa",
            "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions"
        )

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario

    list_display = ("username", "email", "empresa", "is_staff", "is_active")
    list_filter = ("empresa", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email")
    ordering = ("username",)

    # ✅ edición (cuando ya existe)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email")}),
        ("Empresa", {"fields": ("empresa",)}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    # ✅ creación (cuando le das "Agregar usuario")
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "empresa", "password1", "password2", "is_active", "is_staff"),
        }),
    )

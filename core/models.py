# core/models.py - VERSIÓN CORREGIDA
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.utils import timezone
from decimal import Decimal

# 1. Usuario personalizado
class Usuario(AbstractUser):
    def get_roles():
        return [(g.name.lower(), g.name) for g in Group.objects.all()]

    rol = models.CharField(max_length=50, choices=get_roles, blank=True, null=True)

    def __str__(self):
        return self.username


# 2. Cliente
class Cliente(models.Model):
    nombre    = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True)
    telefono  = models.CharField(max_length=20, blank=True)
    correo    = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre


# 3. Catálogo: categoría, proveedor y CAI
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre    = models.CharField(max_length=100)
    direccion = models.TextField(blank=True)
    telefono  = models.CharField(max_length=20, blank=True)
    correo    = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre


class Cai(models.Model):
    codigo               = models.CharField("Código CAI", max_length=50, unique=True)
    rango_inicial        = models.PositiveIntegerField("Correlativo inicial")
    rango_final          = models.PositiveIntegerField("Correlativo final")
    correlativo_actual   = models.PositiveIntegerField("Siguiente correlativo")
    fecha_limite         = models.DateField("Fecha límite de emisión")
    activo               = models.BooleanField("Activo", default=True)

    def __str__(self):
        return f"{self.codigo} — {self.correlativo_actual}/{self.rango_final}"


# 4. Producto UNIFICADO Y CORREGIDO
class Producto(models.Model):
    codigo       = models.CharField(max_length=50, unique=True, verbose_name="Código o ID")
    codigo_barra = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Código de barra")
    nombre       = models.CharField(max_length=100)
    descripcion  = models.TextField(blank=True)
    precio       = models.DecimalField(max_digits=10, decimal_places=2)
    stock        = models.IntegerField(default=0)
    categoria    = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True)  # Temporal
    activo       = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Temporal

    def __str__(self):
        return f"{self.nombre} - L{self.precio} ({self.codigo})"
    
    @property
    def necesita_restock(self):
        return self.stock <= 5
    
    class Meta:
        ordering = ['nombre']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"



class Cotizacion(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, default="pendiente")  # pendiente, facturada

    def __str__(self):
        return f"Cotización #{self.id} - {self.cliente.nombre}"


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        precio_final = self.precio_unitario
        if self.descuento > 0:
            precio_final = precio_final - (precio_final * (self.descuento / Decimal('100')))
        self.subtotal = self.cantidad * precio_final
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"



# 5. Venta 
class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    cliente = models.ForeignKey(
        'Cliente',  # o core.Cliente si está en otro app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None
    )

    tipo_pago = models.CharField(
        max_length=10,
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        default='contado'
    )

    cai = models.ForeignKey(
        'CAI',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    numero_factura = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        num = f"#{self.numero_factura}" if self.numero_factura else "(sin nº)"
        return f"Venta {num} – {self.fecha.strftime('%d/%m/%Y')}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # precio original
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # % descuento
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        precio_final = self.precio_unitario
        if self.descuento > 0:
            precio_final = precio_final - (precio_final * (self.descuento / 100))
        self.subtotal = self.cantidad * precio_final
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"



# 7. Compra
class Compra(models.Model):
    fecha      = models.DateTimeField(auto_now_add=True)
    proveedor  = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    total      = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago  = models.CharField(
        max_length=10,
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        default='contado'
    )


class DetalleCompra(models.Model):
    compra         = models.ForeignKey(Compra, on_delete=models.CASCADE)
    producto       = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad       = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal       = models.DecimalField(max_digits=10, decimal_places=2)


# 8. Cuentas por Cobrar y por Pagar (OPCIONAL POR AHORA)
class CuentaPorCobrar(models.Model):
    cliente           = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    venta             = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='cuentaporcobrar'  # 🔹 Esto permite venta.cuentaporcobrar.all() o .first()
    )
    monto_pendiente   = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado            = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')]
    )
    fecha_pago        = models.DateField(null=True, blank=True)
    monto_pagado      = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"CxC {self.venta.numero_factura} – {self.estado}"



class CuentaPorPagar(models.Model):
    proveedor         = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    compra            = models.ForeignKey(Compra, on_delete=models.CASCADE)
    monto_pendiente   = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado            = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')]
    )
    fecha_pago        = models.DateField(null=True, blank=True)
    monto_pagado      = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"CxP {self.compra.id} – {self.estado}"
  


class Empleado(models.Model):
    nombre = models.CharField(max_length=150)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ingreso = models.DateField(default=timezone.now)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.puesto})"


class PagoEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pago {self.monto} a {self.empleado.nombre} el {self.fecha_pago}"


   
 




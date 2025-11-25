# core/models.py - VERSIÓN CORREGIDA
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.utils import timezone
from decimal import Decimal
from django.conf import settings

# 1. Usuario personalizado
class Usuario(AbstractUser):
    def get_roles():
        return [(g.name.lower(), g.name) for g in Group.objects.all()]

    rol = models.CharField(max_length=50, choices=get_roles, blank=True, null=True)

    def __str__(self):
        return self.username


# 2. Cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre



# 3. Catálogo: categoría, proveedor y CAI
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


# ============= PROVEEDOR MEJORADO =============
class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Razón Social")
    rtn = models.CharField(max_length=20, blank=True, null=True, verbose_name="RTN")
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    contacto = models.CharField(max_length=100, blank=True, help_text="Nombre del contacto principal")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre



# 4. Producto UNIFICADO Y CORREGIDO
class Producto(models.Model):
    TIPO_IMPUESTO_CHOICES = [
        ('E', 'Exento'),
        ('G15', 'Gravado 15%'),
        ('G18', 'Gravado 18%'),
        ('EXO', 'Exonerado'),  # si necesitas distinguir
    ]

    codigo       = models.CharField(max_length=50, unique=True, verbose_name="Código o ID")
    codigo_barra = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Código de barra")
    nombre       = models.CharField(max_length=100)
    descripcion  = models.TextField(blank=True)
    precio       = models.DecimalField(max_digits=10, decimal_places=2)
    stock        = models.IntegerField(default=0)
    categoria    = models.ForeignKey('Categoria', on_delete=models.CASCADE, null=True, blank=True)
    activo       = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tipo_impuesto = models.CharField(max_length=4, choices=TIPO_IMPUESTO_CHOICES, default='E')

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



class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Campos fiscales nuevos
    subtotal_exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    impuesto_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    cliente = models.ForeignKey(
        'Cliente',
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
        'Cai',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    numero_factura = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"Venta #{self.numero_factura or 'sin número'}"



class Cai(models.Model):
    codigo = models.CharField("Código CAI", max_length=50, unique=True)

    prefijo = models.CharField("Prefijo SAR", max_length=20, blank=True, null=True)

    rango_inicial = models.PositiveIntegerField("Correlativo inicial")
    rango_final = models.PositiveIntegerField("Correlativo final")
    correlativo_actual = models.PositiveIntegerField("Siguiente correlativo")

    fecha_limite = models.DateField("Fecha límite de emisión")
    activo = models.BooleanField("Activo", default=True)


    def asignar_siguiente_correlativo(self):
        """Aumenta correlativo y valida rango SAR"""
        if self.correlativo_actual > self.rango_final:
            raise ValueError("CAI fuera del rango permitido")

        correlativo = self.correlativo_actual
        self.correlativo_actual += 1
        self.save(update_fields=['correlativo_actual'])
        return correlativo


    def get_numero_formateado(self, numero):
        """Devuelve prefijo + correlativo de 8 dígitos"""
        correlativo = str(numero).zfill(8)
        pref = self.prefijo if self.prefijo else ""
        return f"{pref}{correlativo}"

  

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # precio original
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # % descuento
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # subtotal sin impuesto
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # monto de impuesto (ISV)
    total_linea = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # subtotal + impuesto

    def save(self, *args, **kwargs):
        precio_final = self.precio_unitario
        if self.descuento > 0:
            precio_final = precio_final - (precio_final * (self.descuento / Decimal('100')))

        # subtotal sin impuesto
        self.subtotal = (Decimal(self.cantidad) * precio_final).quantize(Decimal('0.01'))

        # determinar impuesto según tipo del producto
        tipo = self.producto.tipo_impuesto if self.producto and hasattr(self.producto, 'tipo_impuesto') else 'E'

        impuesto_amount = Decimal('0.00')
        if tipo == 'G15':
            impuesto_amount = (self.subtotal * Decimal('0.15')).quantize(Decimal('0.01'))
        elif tipo == 'G18':
            impuesto_amount = (self.subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        # exento o exonerado -> impuesto 0

        self.impuesto = impuesto_amount
        self.total_linea = (self.subtotal + self.impuesto).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"



# ============= COMPRA MEJORADA =============
class Compra(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada')
    ]
    
    # Identificación
    numero_compra = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    numero_factura_proveedor = models.CharField(max_length=50, blank=True, verbose_name="# Factura Proveedor")
    
    # Relaciones
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    
    # Fechas
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_recepcion = models.DateField(null=True, blank=True, help_text="Fecha en que se recibió la mercancía")
    
    # Montos - Subtotales por tipo de impuesto
    subtotal_exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Subtotal Gravado 15%")
    subtotal_g18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Subtotal Gravado 18%")
    
    # Impuestos calculados
    impuesto_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Total
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Pago y estado
    tipo_pago = models.CharField(
        max_length=10,
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        default='contado'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # Observaciones
    notas = models.TextField(blank=True, help_text="Observaciones o notas adicionales")

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = "Compras"

    def __str__(self):
        return f"Compra #{self.numero_compra or self.id} - {self.proveedor}"

    def save(self, *args, **kwargs):
        if not self.numero_compra:
            # Generar número de compra automático: COM-000001
            ultima = Compra.objects.all().order_by('-id').first()
            if ultima and ultima.numero_compra:
                try:
                    ultimo_num = int(ultima.numero_compra.split('-')[1])
                    self.numero_compra = f"COM-{ultimo_num + 1:06d}"
                except:
                    self.numero_compra = "COM-000001"
            else:
                self.numero_compra = "COM-000001"
        super().save(*args, **kwargs)


# ============= DETALLE COMPRA MEJORADO =============
class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), help_text="Descuento en porcentaje")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

    def calcular_subtotal(self):
        """Calcula el subtotal considerando descuento"""
        base = self.precio_unitario * self.cantidad
        descuento_monto = base * (self.descuento / Decimal('100'))
        return base - descuento_monto

    def save(self, *args, **kwargs):
        self.subtotal = self.calcular_subtotal()
        super().save(*args, **kwargs)
        

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
    
       # ✅ AGREGAR ESTA PROPIEDAD
    @property
    def saldo_restante(self):
        """Calcula cuánto falta por pagar"""
        return self.monto_pendiente - self.monto_pagado
    

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
    
     # ✅ AGREGAR ESTA PROPIEDAD
    @property
    def saldo_restante(self):
        """Calcula cuánto falta por pagar"""
        return self.monto_pendiente - self.monto_pagado

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


class EmpresaConfig(models.Model):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)

    # Para que solo exista 1 registro
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración del negocio"



class Pago(models.Model):
    METODOS = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]

    venta = models.ForeignKey('Venta', on_delete=models.CASCADE, related_name='pagos')
    metodo = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True, null=True,
                                  help_text="Número de referencia o autorización (tarjeta/transferencia)")

    def __str__(self):
        return f"{self.get_metodo_display()} L {self.monto} — Venta {self.venta_id}"
   
 




# core/models.py - VERSIÓN CORREGIDA
from django.db import models
from decimal import Decimal
from django.conf import settings


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
    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.PROTECT)
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
    compra = models.ForeignKey('compras.Compra', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
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
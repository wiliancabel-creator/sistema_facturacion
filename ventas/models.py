from django.db import models
from decimal import Decimal
from core.models import Empresa


class Venta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="ventas")  # ✅

    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    subtotal_exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    impuesto_15 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_18 = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    cliente = models.ForeignKey(
        'clientes.Cliente',
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
        'cai.Cai',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    numero_factura = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"Venta #{self.numero_factura or self.id}"


class DetalleVenta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="detalle_ventas")  # ✅
    
    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)

    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_linea = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        precio_final = self.precio_unitario
        if self.descuento and self.descuento > 0:
            precio_final = precio_final - (precio_final * (self.descuento / Decimal('100')))

        self.subtotal = (Decimal(self.cantidad) * precio_final).quantize(Decimal('0.01'))

        tipo = getattr(self.producto, 'tipo_impuesto', 'E') or 'E'
        impuesto_amount = Decimal('0.00')
        if tipo == 'G15':
            impuesto_amount = (self.subtotal * Decimal('0.15')).quantize(Decimal('0.01'))
        elif tipo == 'G18':
            impuesto_amount = (self.subtotal * Decimal('0.18')).quantize(Decimal('0.01'))

        self.impuesto = impuesto_amount
        self.total_linea = (self.subtotal + self.impuesto).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"


class Pago(models.Model):
    
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="pagos")  # ✅
    
    METODOS = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('otro', 'Otro'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="pagos"
    )

    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='pagos')
    metodo = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_metodo_display()} L {self.monto} — Venta {self.venta_id}"

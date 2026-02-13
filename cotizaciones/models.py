# core/models.py - VERSIÓN CORREGIDA
from django.db import models
from decimal import Decimal



class Cotizacion(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True, default=None)

    tipo_pago = models.CharField(
        max_length=10,
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        default='contado'
    )

    # Totales fiscales (igual que Venta)
    subtotal_exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g15    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g18    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_15     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_18     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    estado = models.CharField(max_length=20, default="pendiente")  # pendiente, facturada

    def __str__(self):
        return f"Cotización #{self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"


class DetalleCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Igual que DetalleVenta
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # sin impuesto
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # ISV
    total_linea = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # subtotal+impuesto

    def save(self, *args, **kwargs):
        precio_final = self.precio_unitario
        if self.descuento and self.descuento > 0:
            precio_final = precio_final - (precio_final * (Decimal(self.descuento) / Decimal('100')))

        self.subtotal = (Decimal(self.cantidad) * Decimal(precio_final)).quantize(Decimal('0.01'))

        tipo = self.producto.tipo_impuesto if self.producto and hasattr(self.producto, 'tipo_impuesto') else 'E'

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

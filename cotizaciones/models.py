from django.db import models
from decimal import Decimal
from core.models import Empresa

class Cotizacion(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="cotizaciones"
    )

    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL, null=True, blank=True, default=None)

    tipo_pago = models.CharField(
        max_length=10,
        choices=[('contado', 'Contado'), ('credito', 'Crédito')],
        default='contado'
    )

    subtotal_exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g15    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    subtotal_g18    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_15     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto_18     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    estado = models.CharField(max_length=20, default="pendiente")

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Cotización #{self.id} - {self.cliente.nombre if self.cliente else 'Sin cliente'}"


class DetalleCotizacion(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="detalle_cotizaciones"
    )

    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)

    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_linea = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        # ... tu cálculo igual ...
        super().save(*args, **kwargs)


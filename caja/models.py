from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.conf import settings





class Caja(models.Model):
    nombre = models.CharField(max_length=60, default="Caja Principal")
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class CajaSesion(models.Model):
    ESTADOS = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
        ('anulada', 'Anulada'),
    ]

    caja = models.ForeignKey('caja.Caja', on_delete=models.PROTECT)
    cajero = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    monto_apertura = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Snapshot al cerrar (totales por método)
    total_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_tarjeta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_transferencia = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_otro = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    ingresos_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    egresos_efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    efectivo_teorico = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    efectivo_contado = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    diferencia = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    observacion = models.TextField(blank=True, default='')

    estado = models.CharField(max_length=10, choices=ESTADOS, default='abierta')

    class Meta:
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"{self.caja} - {self.cajero} - {self.fecha_apertura:%Y-%m-%d} ({self.estado})"


class CajaMovimiento(models.Model):
    TIPOS = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]

    sesion = models.ForeignKey(CajaSesion, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    concepto = models.CharField(max_length=120)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.get_tipo_display()} L{self.monto} - {self.concepto}"

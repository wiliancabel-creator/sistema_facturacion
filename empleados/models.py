from django.db import models
from django.utils import timezone
from core.models import Empresa

class Empleado(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="empleados"
    )

    nombre = models.CharField(max_length=150)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_ingreso = models.DateField(default=timezone.now)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.puesto})"


class PagoEmpleado(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="pagos_empleados"
    )

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField(default=timezone.now)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pago {self.monto} a {self.empleado.nombre} el {self.fecha_pago}"


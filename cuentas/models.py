from django.db import models
from core.models import Empresa


class CuentaPorCobrar(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="cuentas_por_cobrar"
    )

    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='cuentaporcobrar')

    monto_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')]
    )
    fecha_pago = models.DateField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def saldo_restante(self):
        return self.monto_pendiente - self.monto_pagado

    def __str__(self):
        return f"CxC {self.venta.numero_factura} – {self.estado}"


class CuentaPorPagar(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="cuentas_por_pagar"
    )

    proveedor = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    compra = models.ForeignKey('compras.Compra', on_delete=models.CASCADE)

    monto_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')]
    )
    fecha_pago = models.DateField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def saldo_restante(self):
        return self.monto_pendiente - self.monto_pagado

    def __str__(self):
        return f"CxP {self.compra.id} – {self.estado}"

# core/models.py - VERSIÓN CORREGIDA
from django.db import models


# 8. Cuentas por Cobrar y por Pagar (OPCIONAL POR AHORA)
class CuentaPorCobrar(models.Model):
    cliente= models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE)
    venta= models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='cuentaporcobrar')  # 🔹 Esto permite venta.cuentaporcobrar.all() o .first())
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
    proveedor         = models.ForeignKey('proveedores.Proveedor', on_delete=models.CASCADE)
    compra            = models.ForeignKey('compras.Compra', on_delete=models.CASCADE)
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
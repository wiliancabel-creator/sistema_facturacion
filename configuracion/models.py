# core/models.py - VERSIÓN CORREGIDA
from django.db import models


class EmpresaConfig(models.Model):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.CharField(max_length=150, blank=True, null=True)

    moneda = models.CharField(max_length=10, default="L")
    isv_default = models.DecimalField(max_digits=5, decimal_places=2, default=0.15)  # 0.15 o 0.18
    actualizado = models.DateTimeField(auto_now=True)

    # Para que solo exista 1 registro
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración del negocio"


class ModuloConfig(models.Model):
    # ventas
    mod_ventas = models.BooleanField(default=True)
    mod_cotizaciones = models.BooleanField(default=True)

    # inventario/productos
    mod_productos = models.BooleanField(default=True)
    mod_compras = models.BooleanField(default=True)

    # cartera
    mod_cuentas = models.BooleanField(default=True)

    # extras
    mod_empleados = models.BooleanField(default=True)
    mod_cai = models.BooleanField(default=True)
    mod_reportes = models.BooleanField(default=True) # este modulo falta
    mod_caja = models.BooleanField(default=True) # NUEVO MÓDULO CAJA

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Módulos activos"
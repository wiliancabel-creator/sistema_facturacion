# core/models.py - VERSIÓN CORREGIDA
from django.db import models

from core.models import Empresa

class EmpresaConfig(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name="config")
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(max_length=150, blank=True, null=True)

    moneda = models.CharField(max_length=10, default="L")
    isv_default = models.DecimalField(max_digits=5, decimal_places=2, default=0.15)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config {self.empresa.nombre}"



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
# core/models.py - VERSIÓN CORREGIDA
from django.db import models
from core.models import Empresa

class Cliente(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="clientes"
    )

    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


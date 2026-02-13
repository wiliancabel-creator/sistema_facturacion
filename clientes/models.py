# core/models.py - VERSIÓN CORREGIDA
from django.db import models

# 2. Cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

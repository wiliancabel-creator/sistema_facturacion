# core/models.py - VERSIÓN CORREGIDA
from django.db import models




# ============= PROVEEDOR MEJORADO =============
class Proveedor(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre/Razón Social")
    rtn = models.CharField(max_length=20, blank=True, null=True, verbose_name="RTN")
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    contacto = models.CharField(max_length=100, blank=True, help_text="Nombre del contacto principal")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre
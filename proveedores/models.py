from django.db import models
from core.models import Empresa

class Proveedor(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="proveedores"
    )

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
        # ✅ evita choques por empresa (elige lo que te convenga)
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nombre'], name='uniq_proveedor_nombre_por_empresa'),
        ]

    def __str__(self):
        return self.nombre

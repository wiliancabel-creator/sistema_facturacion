# core/models.py - VERSIÓN CORREGIDA
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group


class Empresa(models.Model):
    nombre = models.CharField(max_length=150)
    rtn = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(max_length=150, blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre






class Usuario(AbstractUser):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios"
    )

    @staticmethod
    def get_roles():
        # Mantener por compatibilidad con migraciones viejas
        return [(g.name.lower(), g.name) for g in Group.objects.all()]


    def __str__(self):
        return self.username


   
 
 



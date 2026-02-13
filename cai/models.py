# core/models.py - VERSIÓN CORREGIDA
from django.db import models




class Cai(models.Model):
    codigo = models.CharField("Código CAI", max_length=50, unique=True)

    prefijo = models.CharField("Prefijo SAR", max_length=20, blank=True, null=True)

    rango_inicial = models.PositiveIntegerField("Correlativo inicial")
    rango_final = models.PositiveIntegerField("Correlativo final")
    correlativo_actual = models.PositiveIntegerField("Siguiente correlativo")

    fecha_limite = models.DateField("Fecha límite de emisión")
    activo = models.BooleanField("Activo", default=True)


    def asignar_siguiente_correlativo(self):
        """Aumenta correlativo y valida rango SAR"""
        if self.correlativo_actual > self.rango_final:
            raise ValueError("CAI fuera del rango permitido")

        correlativo = self.correlativo_actual
        self.correlativo_actual += 1
        self.save(update_fields=['correlativo_actual'])
        return correlativo


    def get_numero_formateado(self, numero):
        """Devuelve prefijo + correlativo de 8 dígitos"""
        correlativo = str(numero).zfill(8)
        pref = self.prefijo if self.prefijo else ""
        return f"{pref}{correlativo}"


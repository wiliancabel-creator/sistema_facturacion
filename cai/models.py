from django.db import models
from django.core.exceptions import ValidationError
from core.models import Empresa

class Cai(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="cais"
    )

    codigo = models.CharField("Código CAI", max_length=50)
    prefijo = models.CharField("Prefijo SAR", max_length=20, blank=True, null=True)

    rango_inicial = models.PositiveIntegerField("Correlativo inicial")
    rango_final = models.PositiveIntegerField("Correlativo final")
    correlativo_actual = models.PositiveIntegerField("Siguiente correlativo")

    fecha_limite = models.DateField("Fecha límite de emisión")
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        ordering = ['-activo', 'fecha_limite']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'codigo'], name='uniq_cai_codigo_por_empresa'),
        ]

    def clean(self):
        # Opcional: asegurar correlativo dentro del rango
        if self.correlativo_actual < self.rango_inicial:
            raise ValidationError({"correlativo_actual": "No puede ser menor al rango inicial."})
        if self.rango_final < self.rango_inicial:
            raise ValidationError({"rango_final": "No puede ser menor al rango inicial."})

    def asignar_siguiente_correlativo(self):
        if self.correlativo_actual > self.rango_final:
            raise ValueError("CAI fuera del rango permitido")

        correlativo = self.correlativo_actual
        self.correlativo_actual += 1
        self.save(update_fields=['correlativo_actual'])
        return correlativo

    def get_numero_formateado(self, numero):
        correlativo = str(numero).zfill(8)
        pref = self.prefijo if self.prefijo else ""
        return f"{pref}{correlativo}"


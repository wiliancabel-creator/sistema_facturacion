from django.db import models
from core.models import Empresa


class Categoria(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="categorias"
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ('empresa', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TIPO_IMPUESTO_CHOICES = [
        ('E', 'Exento'),
        ('G15', 'Gravado 15%'),
        ('G18', 'Gravado 18%'),
        ('EXO', 'Exonerado'),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="productos"
    )

    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    codigo = models.CharField(
        max_length=5,
        blank=True,
        db_index=True,
        verbose_name="Código o ID"
    )

    # ⚠️ Nota: con multi-tenant NO puede ser unique global
    # Si quieres que sea único por empresa, lo haremos con UniqueConstraint.
    codigo_barra = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Código de barra"
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tipo_impuesto = models.CharField(max_length=4, choices=TIPO_IMPUESTO_CHOICES, default='E')

    class Meta:
        ordering = ['nombre']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        constraints = [
            # codigo único por empresa (si existe)
            models.UniqueConstraint(fields=['empresa', 'codigo'], name='uniq_producto_codigo_por_empresa'),
            # codigo_barra único por empresa (si existe)
            models.UniqueConstraint(fields=['empresa', 'codigo_barra'], name='uniq_producto_barra_por_empresa'),
        ]

    def __str__(self):
        return f"{self.nombre} - L{self.precio} ({self.codigo})"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)

    def _generar_codigo(self):
        # correlativo por empresa: 00001, 00002...
        ultimo = Producto.objects.filter(empresa=self.empresa).order_by('-id').first()
        siguiente = (int(ultimo.codigo) + 1) if (ultimo and str(ultimo.codigo).isdigit()) else 1
        return str(siguiente).zfill(5)

    @property
    def necesita_restock(self):
        return self.stock <= 5

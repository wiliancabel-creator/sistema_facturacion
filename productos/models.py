# core/models.py - VERSIÓN CORREGIDA
from django.db import models




class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre



# 4. Producto UNIFICADO Y CORREGIDO
class Producto(models.Model):
    TIPO_IMPUESTO_CHOICES = [
        ('E', 'Exento'),
        ('G15', 'Gravado 15%'),
        ('G18', 'Gravado 18%'),
        ('EXO', 'Exonerado'),  # si necesitas distinguir
    ]

    imagen = models.ImageField(upload_to='productos/',null=True,blank=True)
    
    codigo = models.CharField(
    max_length=5,
    unique=True,
    blank=True,      #  permitir vacío en el form
    editable=True,  # que el usuario no lo edite (opcional)
    db_index=True,
    verbose_name="Código o ID"
)

    codigo_barra = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Código de barra")
    nombre       = models.CharField(max_length=100)
    descripcion  = models.TextField(blank=True)
    precio       = models.DecimalField(max_digits=10, decimal_places=2)
    stock        = models.IntegerField(default=0)
    categoria    = models.ForeignKey('Categoria', on_delete=models.CASCADE, null=True, blank=True)
    activo       = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    tipo_impuesto = models.CharField(max_length=4, choices=TIPO_IMPUESTO_CHOICES, default='E')

    def __str__(self):
        return f"{self.nombre} - L{self.precio} ({self.codigo})"
    
    def save(self, *args, **kwargs):
     if not self.codigo:
        self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)

    def _generar_codigo(self):
        # genera correlativo 00001, 00002...
        ultimo = Producto.objects.order_by('-id').first()
        siguiente = (int(ultimo.codigo) + 1) if (ultimo and str(ultimo.codigo).isdigit()) else 1
        return str(siguiente).zfill(5)


    @property
    def necesita_restock(self):
        return self.stock <= 5

    class Meta:
        ordering = ['nombre']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
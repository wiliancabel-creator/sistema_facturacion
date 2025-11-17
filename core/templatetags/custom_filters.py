from django import template
from core.models import Producto  # ✅ tus modelos están en core.models

register = template.Library()

@register.filter
def get_producto_nombre(producto_id):
    """
    Devuelve el nombre del producto a partir de su ID.
    Si no existe, retorna texto vacío.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
        return producto.nombre
    except Producto.DoesNotExist:
        return ""
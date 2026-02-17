from django import forms
from productos.models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # ✅ NO incluimos empresa, se asigna en la vista
        fields = [
            'imagen',
            'codigo',
            'codigo_barra',
            'nombre',
            'descripcion',
            'precio',
            'stock',
            'categoria',
            'activo',
            'tipo_impuesto',
        ]

    def __init__(self, *args, **kwargs):
        # ✅ recibimos empresa desde la vista
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        # (opcional) clases bootstrap
        for f in self.fields.values():
            if not isinstance(f.widget, forms.CheckboxInput):
                f.widget.attrs.setdefault('class', 'form-control')

        # ✅ Filtrar categorías por empresa
        if empresa is not None:
            self.fields['categoria'].queryset = Categoria.objects.filter(empresa=empresa).order_by('nombre')
        else:
            self.fields['categoria'].queryset = Categoria.objects.none()


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'})
        }

from django import forms
from compras.models import DetalleCompra,Compra 



class DetalleCompraForm(forms.ModelForm):
    precio_actual = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        disabled=True,
        label='Precio actual del producto',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DetalleCompra
        fields = ['producto', 'cantidad', 'precio_unitario', 'precio_actual']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control producto-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que producto tenga la clase para Select2
        self.fields['producto'].widget.attrs.update({'class': 'form-control producto-select'})
        

from proveedores.models import Proveedor

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor', 'numero_factura_proveedor', 'tipo_pago', 'fecha_recepcion', 'notas']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'numero_factura_proveedor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: FACT-001'}),
            'tipo_pago': forms.Select(attrs={'class': 'form-select'}),
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones opcionales...'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)  # 👈 recibimos empresa
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields['proveedor'].queryset = Proveedor.objects.filter(
                empresa=empresa,
                activo=True
            )
       
        
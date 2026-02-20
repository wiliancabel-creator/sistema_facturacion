from django import forms
from cotizaciones.models import Cotizacion, DetalleCotizacion 
from productos.models import Producto


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['tipo_pago']  # cliente llega por hidden input



class DetalleCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleCotizacion
        fields = ['producto', 'cantidad', 'precio_unitario', 'descuento']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control','min': '1','value': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control','readonly': True}),
            'descuento': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['producto'].queryset = Producto.objects.filter(
                empresa=empresa,
                activo=True
            ).order_by('nombre')

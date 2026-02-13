from django import forms
from cotizaciones.models import Cotizacion, DetalleCotizacion 



class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['tipo_pago']  # cliente llega por hidden input



class DetalleCotizacionForm(forms.ModelForm):
    class Meta:
        model = DetalleCotizacion
        fields = ['producto', 'cantidad', 'precio_unitario', 'descuento']
        widgets = {
            'producto': forms.HiddenInput(),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'descuento': forms.HiddenInput(),
        }
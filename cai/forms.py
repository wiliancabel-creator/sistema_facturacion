from django import forms
from cai.models import Cai


class CaiForm(forms.ModelForm):
    class Meta:
        model = Cai
        fields = [
            'codigo', 'prefijo', 'rango_inicial',
            'rango_final', 'correlativo_actual',
            'fecha_limite', 'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'prefijo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000-001-01-'}),
            'rango_inicial': forms.NumberInput(attrs={'class': 'form-control'}),
            'rango_final': forms.NumberInput(attrs={'class': 'form-control'}),
            'correlativo_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_limite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
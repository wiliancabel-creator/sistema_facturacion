from django import forms
from configuracion.models import EmpresaConfig

class EmpresaConfigForm(forms.ModelForm):
    class Meta:
        model = EmpresaConfig
        fields = ['nombre', 'rtn', 'direccion', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rtn': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.TextInput(attrs={'class': 'form-control'}),
        }
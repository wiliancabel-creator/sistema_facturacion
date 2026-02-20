from django import forms
from empleados.models import Empleado, PagoEmpleado

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'puesto', 'salario_base', 'fecha_ingreso', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
            'salario_base': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PagoEmpleadoForm(forms.ModelForm):
    class Meta:
        model = PagoEmpleado
        fields = ['empleado', 'fecha_pago', 'monto', 'descripcion']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['empleado'].queryset = Empleado.objects.filter(
                empresa=empresa,
                activo=True
            ).order_by('nombre')

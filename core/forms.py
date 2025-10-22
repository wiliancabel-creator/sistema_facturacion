from django import forms
from .models import Producto,DetalleVenta,DetalleCompra,Proveedor,Compra,Cliente, Categoria, Cotizacion, DetalleCotizacion 
from .models import Venta, Cai, Empleado, PagoEmpleado


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        



class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente']


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

 

# En tu forms.py - SOLO CAMBIAR la clase DetalleVentaForm:

class DetalleVentaForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'readonly': True,
            'class': 'form-control precio-readonly'
        })
    )

    descuento = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario', 'descuento']
        widgets = {
            'producto': forms.HiddenInput(),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        self.fields['producto'].empty_label = "Seleccionar producto..."

        if self.instance.pk and self.instance.producto:
            self.fields['precio_unitario'].initial = self.instance.producto.precio


class ClienteVentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'tipo_pago', 'cai']
        widgets = {
            'cliente':    forms.Select(attrs={'class': 'form-control'}),
            'tipo_pago':  forms.Select(attrs={'class': 'form-control'}),
            'cai':        forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all()
        self.fields['cai'].queryset = Cai.objects.filter(activo=True)

        # 👇 Establecer "CONSUMIDOR FINAL" como cliente por defecto
        try:
            consumidor_final = Cliente.objects.get(nombre__iexact="CONSUMIDOR FINAL")
            self.initial['cliente'] = consumidor_final.id
        except Cliente.DoesNotExist:
            pass





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

        
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'correo']  
        
class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor', 'tipo_pago']
        widgets = {
            'tipo_pago': forms.Select(attrs={'class': 'form-select'})
        }

        
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'direccion', 'telefono', 'correo'] 
                        


class CaiForm(forms.ModelForm):
    class Meta:
        model = Cai
        fields = [
            'codigo', 'rango_inicial', 'rango_final',
            'correlativo_actual', 'fecha_limite', 'activo'
        ]
        widgets = {
            'codigo':            forms.TextInput(attrs={'class': 'form-control'}),
            'rango_inicial':     forms.NumberInput(attrs={'class': 'form-control'}),
            'rango_final':       forms.NumberInput(attrs={'class': 'form-control'}),
            'correlativo_actual':forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_limite':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activo':            forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'})
        }    



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
        
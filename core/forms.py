from django import forms
from .models import Producto,DetalleVenta,DetalleCompra,Proveedor,Compra,Cliente, Categoria, Cotizacion, DetalleCotizacion 
from .models import Venta, Cai, Empleado, PagoEmpleado
from .models import EmpresaConfig, Pago



class PagoForm(forms.Form):
    metodo = forms.ChoiceField(choices=Pago.METODOS, widget=forms.Select(attrs={'class':'form-control form-control-sm'}))
    monto = forms.DecimalField(max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class':'form-control form-control-sm','step':'0.01'}))
    referencia = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control form-control-sm'}))
        

       
        
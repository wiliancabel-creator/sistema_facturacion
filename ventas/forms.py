from django import forms
from clientes.models import Cliente
from productos.models import Producto
from ventas.models import Venta,DetalleVenta,Pago
from cai.models import Cai


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
        self.empresa = kwargs.pop('empresa', None)  # ✅
        super().__init__(*args, **kwargs)

        qs = Producto.objects.filter(activo=True)
        if self.empresa:
            qs = qs.filter(empresa=self.empresa)

        self.fields['producto'].queryset = qs
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
        self.empresa = kwargs.pop('empresa', None)  # ✅
        super().__init__(*args, **kwargs)

        clientes_qs = Cliente.objects.all()
        cai_qs = Cai.objects.filter(activo=True)

        if self.empresa:
            clientes_qs = clientes_qs.filter(empresa=self.empresa)
            cai_qs = cai_qs.filter(empresa=self.empresa)

        self.fields['cliente'].queryset = clientes_qs
        self.fields['cai'].queryset = cai_qs

        # ✅ Consumidor Final por defecto pero SOLO de esta empresa
        if self.empresa:
            consumidor_final = clientes_qs.filter(nombre__iexact="CONSUMIDOR FINAL").first()
        else:
            consumidor_final = Cliente.objects.filter(nombre__iexact="CONSUMIDOR FINAL").first()

        if consumidor_final:
            self.initial['cliente'] = consumidor_final.id
            







class PagoForm(forms.Form):
    metodo = forms.ChoiceField(
        choices=Pago.METODOS,
        widget=forms.Select(attrs={'class':'form-control form-control-sm'})
    )
    monto = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class':'form-control form-control-sm','step':'0.01'})
    )
    referencia = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control form-control-sm'})
    )

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor que 0.")
        return monto

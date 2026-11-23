from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["quantity", "delivery_address", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Informations utiles pour le producteur ou la livraison"}),
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop("product", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()
        self.fields["quantity"].widget.attrs["min"] = "1"
        if self.product:
            self.fields["quantity"].widget.attrs["max"] = str(self.product.quantity)
            self.fields["quantity"].help_text = f"Disponible : {self.product.quantity} {self.product.get_unit_display()}"

    def clean_quantity(self):
        qty = self.cleaned_data["quantity"]
        if qty < 1:
            raise forms.ValidationError("La quantité doit être au moins 1.")
        if self.product and qty > self.product.quantity:
            raise forms.ValidationError("Quantité demandée supérieure au stock disponible.")
        return qty


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        allowed = []
        current = self.instance.status
        transitions = {
            Order.Status.EN_ATTENTE: [Order.Status.CONFIRMEE, Order.Status.ANNULEE],
            Order.Status.CONFIRMEE: [Order.Status.EN_LIVRAISON, Order.Status.ANNULEE],
            Order.Status.EN_LIVRAISON: [Order.Status.LIVREE],
            Order.Status.LIVREE: [],
            Order.Status.ANNULEE: [],
        }
        for status in transitions.get(current, []):
            if self.instance.can_transition_to(status, user):
                allowed.append((status, dict(Order.Status.choices)[status]))
        self.fields["status"].choices = [("", "Choisir un statut")] + allowed
        self.fields["status"].widget.attrs["class"] = "form-control form-select"

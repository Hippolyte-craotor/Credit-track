from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "unit", "quantity", "location", "image", "is_available"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-control"
            if isinstance(field.widget, forms.Select):
                css = "form-control form-select"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            if isinstance(field.widget, forms.FileInput):
                css = "form-control"
            field.widget.attrs["class"] = css
        self.fields["price"].widget.attrs["min"] = "0"
        self.fields["quantity"].widget.attrs["min"] = "0"
        self.fields["image"].widget.attrs["accept"] = "image/*"

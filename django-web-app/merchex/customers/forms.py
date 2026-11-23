from django import forms
from .models import Customer


def style_form(form):
    for field in form.fields.values():
        css = "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
        existing = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (existing + " " + css).strip()
    return form


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["display_name", "phone", "address", "note"]
        labels = {
            "display_name": "Nom / Raison sociale",
            "phone": "Téléphone",
            "address": "Adresse (facultatif)",
            "note": "Note (facultatif)",
        }
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

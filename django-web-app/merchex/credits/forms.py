from django import forms
from django.utils import timezone

from customers.models import Customer
from .models import Credit, Payment


def style_form(form):
    for name, field in form.fields.items():
        css = "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "rounded border-slate-300 text-brand-700"
        else:
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()
    return form


class CreditForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.none(), label="Client")
    description = forms.CharField(label="Marchandises / description", max_length=255)
    total_amount = forms.IntegerField(label="Montant total (FCFA)", min_value=1)
    initial_payment = forms.IntegerField(label="Payé immédiatement (FCFA)", min_value=0, required=False, initial=0)
    credit_date = forms.DateField(label="Date", initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}))
    due_date = forms.DateField(label="Échéance (facultatif)", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    note = forms.CharField(label="Observation (facultatif)", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, merchant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(merchant=merchant, is_active=True).order_by("display_name")
        style_form(self)

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get("total_amount") or 0
        initial = cleaned.get("initial_payment") or 0
        if initial > total:
            self.add_error("initial_payment", "Le paiement initial ne peut pas dépasser le montant total.")
        cleaned["initial_payment"] = initial
        return cleaned


class PaymentForm(forms.Form):
    credit = forms.ModelChoiceField(queryset=Credit.objects.none(), label="Crédit")
    amount = forms.IntegerField(label="Montant reçu (FCFA)", min_value=1)
    payment_date = forms.DateField(label="Date", initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"}))
    method = forms.ChoiceField(label="Mode", choices=Payment.Method.choices, initial=Payment.Method.CASH)
    note = forms.CharField(label="Note (facultatif)", required=False)

    def __init__(self, *args, merchant=None, credit=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Credit.objects.filter(merchant=merchant, is_voided=False).exclude(status=Credit.Status.PAID).select_related("customer").order_by("-created_at")
        self.fields["credit"].queryset = qs
        if credit:
            self.fields["credit"].initial = credit
            self.fields["credit"].widget = forms.HiddenInput()
        style_form(self)

    def clean(self):
        cleaned = super().clean()
        credit = cleaned.get("credit")
        amount = cleaned.get("amount") or 0
        if credit and amount > credit.remaining_amount:
            self.add_error("amount", "Le remboursement ne peut pas dépasser le reste à payer.")
        return cleaned


class VoidForm(forms.Form):
    reason = forms.CharField(label="Motif d'annulation", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

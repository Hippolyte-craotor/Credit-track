from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm

from .models import Merchant, User


def style_form(form):
    for field in form.fields.values():
        css = "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "rounded border-slate-300 text-brand-700"
        else:
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()
    return form


class RegisterForm(forms.ModelForm):
    business_name = forms.CharField(label="Nom de la boutique / commerce", max_length=150)
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["full_name", "email"]
        labels = {"full_name": "Nom complet", "email": "Adresse e-mail"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") and cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        merchant = Merchant.objects.create(name=self.cleaned_data["business_name"].strip())
        user.merchant = merchant
        user.role = User.Role.OWNER
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)
        style_form(self)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").lower()
        password = cleaned.get("password")
        if email and password:
            self.user = authenticate(username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Adresse e-mail ou mot de passe incorrect.")
            if not self.user.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
        return cleaned

    def get_user(self):
        return self.user


class ProfileForm(forms.ModelForm):
    business_name = forms.CharField(label="Nom du commerce", max_length=150)

    class Meta:
        model = User
        fields = ["full_name", "email"]
        labels = {"full_name": "Nom complet", "email": "Adresse e-mail"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.merchant_id:
            self.fields["business_name"].initial = self.instance.merchant.name
        style_form(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            merchant = user.merchant
            merchant.name = self.cleaned_data["business_name"].strip()
            merchant.save(update_fields=["name"])
        return user


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_form(self)

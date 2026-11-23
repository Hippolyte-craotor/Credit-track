from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import BuyerProfile, ProducerProfile, TransporterProfile, User


class UserRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Roles.PRODUCTEUR, "Producteur"),
            (User.Roles.ACHETEUR, "Acheteur"),
            (User.Roles.TRANSPORTEUR, "Transporteur"),
        ],
        label="Je suis",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "city",
            "address",
            "role",
            "password1",
            "password2",
        ]
        labels = {
            "username": "Nom d'utilisateur",
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()
            if name == "role":
                field.widget.attrs["class"] = "form-control form-select"
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            self.create_profile(user)
        return user

    def create_profile(self, user):
        if user.role == User.Roles.PRODUCTEUR:
            ProducerProfile.objects.get_or_create(user=user)
        elif user.role == User.Roles.ACHETEUR:
            BuyerProfile.objects.get_or_create(user=user)
        elif user.role == User.Roles.TRANSPORTEUR:
            TransporterProfile.objects.get_or_create(user=user)


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "city", "address"]
        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ProducerProfileForm(forms.ModelForm):
    class Meta:
        model = ProducerProfile
        fields = ["farm_name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ["company_name", "business_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class TransporterProfileForm(forms.ModelForm):
    class Meta:
        model = TransporterProfile
        fields = ["company_name", "vehicle_type", "coverage_area", "capacity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

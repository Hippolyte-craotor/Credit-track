from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    BuyerProfileForm,
    LoginForm,
    ProducerProfileForm,
    TransporterProfileForm,
    UserRegistrationForm,
    UserUpdateForm,
)
from .models import BuyerProfile, ProducerProfile, TransporterProfile, User


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte a été créé avec succès. Bienvenue sur AgriConnect !")
            return redirect("dashboard:home")
        messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Connexion réussie.")
            next_url = request.GET.get("next") or "dashboard:home"
            return redirect(next_url)
        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté.")
    return redirect("home")


def _get_profile_form(request):
    user = request.user
    if user.role == User.Roles.PRODUCTEUR:
        profile, _ = ProducerProfile.objects.get_or_create(user=user)
        return ProducerProfileForm, profile, "producer_form"
    if user.role == User.Roles.ACHETEUR:
        profile, _ = BuyerProfile.objects.get_or_create(user=user)
        return BuyerProfileForm, profile, "buyer_form"
    if user.role == User.Roles.TRANSPORTEUR:
        profile, _ = TransporterProfile.objects.get_or_create(user=user)
        return TransporterProfileForm, profile, "transporter_form"
    return None, None, None


@login_required
def profile(request):
    FormClass, profile_obj, form_key = _get_profile_form(request)
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = FormClass(request.POST, instance=profile_obj) if FormClass else None
        valid_profile = profile_form.is_valid() if profile_form else True
        if user_form.is_valid() and valid_profile:
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("accounts:profile")
        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = FormClass(instance=profile_obj) if FormClass else None
    return render(
        request,
        "accounts/profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )

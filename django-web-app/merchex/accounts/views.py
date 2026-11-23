from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, RegisterForm, StyledPasswordChangeForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Votre compte a été créé avec succès.")
        return redirect("dashboard:index")
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "dashboard:index")
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    password_form = StyledPasswordChangeForm(request.user, request.POST or None, prefix="pwd")
    if request.method == "POST" and "save_profile" in request.POST and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour.")
        return redirect("accounts:profile")
    if request.method == "POST" and "change_password" in request.POST and password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Mot de passe modifié.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form, "password_form": password_form})

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Merchant(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nom commercial")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    country = models.CharField(max_length=2, default="TG", verbose_name="Pays")
    currency = models.CharField(max_length=3, default="XOF", verbose_name="Devise")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commerçant"
        verbose_name_plural = "Commerçants"

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Propriétaire"
        EMPLOYEE = "EMPLOYEE", "Employé"

    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="users", null=True, blank=True
    )
    email = models.EmailField(unique=True, verbose_name="Adresse e-mail")
    full_name = models.CharField(max_length=150, verbose_name="Nom complet")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.full_name or self.email

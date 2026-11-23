from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        PRODUCTEUR = "PRODUCTEUR", "Producteur"
        ACHETEUR = "ACHETEUR", "Acheteur"
        TRANSPORTEUR = "TRANSPORTEUR", "Transporteur"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.ACHETEUR)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    city = models.CharField("Ville / Région", max_length=120, blank=True)
    is_verified = models.BooleanField("Compte vérifié", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_producteur(self):
        return self.role == self.Roles.PRODUCTEUR

    @property
    def is_acheteur(self):
        return self.role == self.Roles.ACHETEUR

    @property
    def is_transporteur(self):
        return self.role == self.Roles.TRANSPORTEUR

    @property
    def is_admin_role(self):
        return self.role == self.Roles.ADMIN or self.is_superuser


class ProducerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="producer_profile")
    farm_name = models.CharField("Nom de l'exploitation", max_length=150, blank=True)
    description = models.TextField("Description", blank=True)

    class Meta:
        verbose_name = "Profil producteur"
        verbose_name_plural = "Profils producteurs"

    def __str__(self):
        return self.farm_name or self.user.username


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="buyer_profile")
    company_name = models.CharField("Nom de l'entreprise", max_length=150, blank=True)
    business_type = models.CharField("Type d'activité", max_length=120, blank=True)

    class Meta:
        verbose_name = "Profil acheteur"
        verbose_name_plural = "Profils acheteurs"

    def __str__(self):
        return self.company_name or self.user.username


class TransporterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="transporter_profile")
    company_name = models.CharField("Nom de l'entreprise", max_length=150, blank=True)
    vehicle_type = models.CharField("Type de véhicule", max_length=120, blank=True)
    coverage_area = models.CharField("Zone de couverture", max_length=255, blank=True)
    capacity = models.CharField("Capacité", max_length=120, blank=True)

    class Meta:
        verbose_name = "Profil transporteur"
        verbose_name_plural = "Profils transporteurs"

    def __str__(self):
        return self.company_name or self.user.username

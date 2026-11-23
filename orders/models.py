from django.conf import settings
from django.db import models

from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        CONFIRMEE = "CONFIRMEE", "Confirmée"
        EN_LIVRAISON = "EN_LIVRAISON", "En livraison"
        LIVREE = "LIVREE", "Livrée"
        ANNULEE = "ANNULEE", "Annulée"

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        limit_choices_to={"role": "ACHETEUR"},
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_orders",
        related_query_name="received_order",
    )
    quantity = models.PositiveIntegerField("Quantité")
    unit_price = models.DecimalField("Prix unitaire", max_digits=12, decimal_places=2)
    total_price = models.DecimalField("Prix total", max_digits=12, decimal_places=2)
    status = models.CharField("Statut", max_length=20, choices=Status.choices, default=Status.EN_ATTENTE)
    delivery_address = models.CharField("Adresse de livraison", max_length=255)
    note = models.TextField("Note", blank=True)
    transporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
        limit_choices_to={"role": "TRANSPORTEUR"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande #{self.pk} - {self.product.name}"

    def can_transition_to(self, new_status, user):
        if user.is_superuser or user.role == "ADMIN":
            return True
        allowed = {
            self.Status.EN_ATTENTE: {
                self.Status.CONFIRMEE: ["PRODUCTEUR"],
                self.Status.ANNULEE: ["PRODUCTEUR", "ACHETEUR"],
            },
            self.Status.CONFIRMEE: {
                self.Status.EN_LIVRAISON: ["PRODUCTEUR", "TRANSPORTEUR", "ADMIN"],
                self.Status.ANNULEE: ["PRODUCTEUR", "ADMIN"],
            },
            self.Status.EN_LIVRAISON: {
                self.Status.LIVREE: ["PRODUCTEUR", "TRANSPORTEUR", "ADMIN"],
            },
        }
        roles = allowed.get(self.status, {}).get(new_status, [])
        return user.role in roles

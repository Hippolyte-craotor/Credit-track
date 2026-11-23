from django.conf import settings
from django.db import models


class Product(models.Model):
    class Category(models.TextChoices):
        CEREALES = "CEREALES", "Céréales"
        LEGUMES = "LEGUMES", "Légumes"
        FRUITS = "FRUITS", "Fruits"
        TUBERCULES = "TUBERCULES", "Tubercules"
        LEGUMINEUSES = "LEGUMINEUSES", "Légumineuses"
        VOLAILLE = "VOLAILLE", "Volaille & Élevage"
        AUTRE = "AUTRE", "Autre"

    class Unit(models.TextChoices):
        KG = "KG", "Kg"
        TONNE = "TONNE", "Tonne"
        SAC = "SAC", "Sac"
        CAISSE = "CAISSE", "Caisse"
        PIECE = "PIECE", "Pièce"
        LITRE = "LITRE", "Litre"

    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        limit_choices_to={"role": "PRODUCTEUR"},
    )
    name = models.CharField("Nom du produit", max_length=150)
    category = models.CharField("Catégorie", max_length=30, choices=Category.choices, default=Category.AUTRE)
    description = models.TextField("Description", blank=True)
    price = models.DecimalField("Prix", max_digits=12, decimal_places=2)
    unit = models.CharField("Unité", max_length=20, choices=Unit.choices, default=Unit.KG)
    quantity = models.PositiveIntegerField("Quantité disponible", default=0)
    location = models.CharField("Localisation", max_length=150)
    image = models.ImageField("Photo", upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField("Disponible", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.producer.username}"

    @property
    def in_stock(self):
        return self.is_available and self.quantity > 0

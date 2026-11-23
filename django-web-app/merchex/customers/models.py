from django.db import models


class Customer(models.Model):
    merchant = models.ForeignKey(
        "accounts.Merchant", on_delete=models.CASCADE, related_name="customers"
    )
    display_name = models.CharField(max_length=150, verbose_name="Nom / Raison sociale")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    address = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    note = models.TextField(blank=True, verbose_name="Note")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["merchant", "display_name"]),
            models.Index(fields=["merchant", "phone"]),
        ]

    def __str__(self):
        return self.display_name

    @property
    def total_remaining(self):
        from credits.models import Credit

        return (
            Credit.objects.filter(merchant=self.merchant, customer=self, is_voided=False)
            .exclude(status=Credit.Status.PAID)
            .aggregate(total=models.Sum("remaining_amount"))["total"]
            or 0
        )

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


class Credit(models.Model):
    class Status(models.TextChoices):
        ONGOING = "ONGOING", "En cours"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partiellement payé"
        PAID = "PAID", "Réglé"
        OVERDUE = "OVERDUE", "En retard"
        VOIDED = "VOIDED", "Annulé"

    merchant = models.ForeignKey(
        "accounts.Merchant", on_delete=models.CASCADE, related_name="credits"
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT, related_name="credits"
    )
    reference = models.CharField(max_length=30, verbose_name="Référence")
    description = models.CharField(max_length=255, verbose_name="Description")
    total_amount = models.PositiveBigIntegerField(verbose_name="Montant total (FCFA)")
    initial_payment = models.PositiveBigIntegerField(default=0, verbose_name="Paiement initial (FCFA)")
    paid_amount = models.PositiveBigIntegerField(default=0, verbose_name="Montant payé (FCFA)")
    remaining_amount = models.PositiveBigIntegerField(default=0, verbose_name="Reste à payer (FCFA)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING, db_index=True)
    credit_date = models.DateField(default=timezone.localdate, verbose_name="Date du crédit")
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance")
    note = models.TextField(blank=True, verbose_name="Observation")
    is_voided = models.BooleanField(default=False)
    void_reason = models.TextField(blank=True, verbose_name="Motif d'annulation")
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="voided_credits"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_credits"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Crédit"
        verbose_name_plural = "Crédits"
        ordering = ["-credit_date", "-created_at"]
        indexes = [
            models.Index(fields=["merchant", "status"]),
            models.Index(fields=["merchant", "customer"]),
            models.Index(fields=["merchant", "due_date"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["merchant", "reference"], name="uniq_credit_reference_per_merchant"),
        ]

    def __str__(self):
        return f"{self.reference} - {self.customer}"

    def recompute_amounts(self, save=True):
        payments_total = (
            self.payments.filter(is_voided=False).aggregate(total=Sum("amount"))["total"] or 0
        )
        self.paid_amount = int(self.initial_payment) + int(payments_total)
        self.remaining_amount = max(int(self.total_amount) - int(self.paid_amount), 0)
        self.recompute_status(save=False)
        if save:
            self.save(update_fields=["paid_amount", "remaining_amount", "status", "updated_at"])

    def recompute_status(self, save=False):
        if self.is_voided:
            self.status = self.Status.VOIDED
        elif self.remaining_amount <= 0:
            self.status = self.Status.PAID
            self.remaining_amount = 0
        elif self.due_date and self.due_date < timezone.localdate():
            self.status = self.Status.OVERDUE
        elif self.paid_amount > 0:
            self.status = self.Status.PARTIALLY_PAID
        else:
            self.status = self.Status.ONGOING
        if save:
            self.save(update_fields=["status", "updated_at"])

    @property
    def is_overdue(self):
        return self.status == self.Status.OVERDUE

    @property
    def status_label(self):
        return self.get_status_display()


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Espèces"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
        TRANSFER = "TRANSFER", "Virement"
        OTHER = "OTHER", "Autre"

    merchant = models.ForeignKey(
        "accounts.Merchant", on_delete=models.CASCADE, related_name="payments"
    )
    credit = models.ForeignKey(Credit, on_delete=models.PROTECT, related_name="payments")
    amount = models.PositiveBigIntegerField(verbose_name="Montant (FCFA)")
    payment_date = models.DateField(default=timezone.localdate, verbose_name="Date du paiement")
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH, verbose_name="Mode")
    note = models.CharField(max_length=255, blank=True, verbose_name="Note")
    is_voided = models.BooleanField(default=False)
    void_reason = models.TextField(blank=True, verbose_name="Motif d'annulation")
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="voided_payments"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_payments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"{self.amount} FCFA - {self.credit.reference}"

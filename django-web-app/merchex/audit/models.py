from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE_CREDIT = "CREATE_CREDIT", "Création crédit"
        UPDATE_CREDIT = "UPDATE_CREDIT", "Modification crédit"
        VOID_CREDIT = "VOID_CREDIT", "Annulation crédit"
        ADD_PAYMENT = "ADD_PAYMENT", "Remboursement"
        VOID_PAYMENT = "VOID_PAYMENT", "Annulation remboursement"
        CREATE_CUSTOMER = "CREATE_CUSTOMER", "Création client"
        UPDATE_CUSTOMER = "UPDATE_CUSTOMER", "Modification client"

    merchant = models.ForeignKey(
        "accounts.Merchant", on_delete=models.CASCADE, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=64)
    summary = models.CharField(max_length=255)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.get_action_display()}"

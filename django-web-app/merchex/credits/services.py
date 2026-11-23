from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from audit.models import AuditLog
from audit.services import log_action

from .models import Credit, Payment


class CreditError(ValueError):
    pass


def generate_credit_reference(merchant):
    year = timezone.localdate().year
    prefix = f"CR-{year}-"
    last = Credit.objects.filter(merchant=merchant, reference__startswith=prefix).aggregate(m=Max("reference"))["m"]
    if last:
        try:
            seq = int(last.split("-")[-1]) + 1
        except Exception:
            seq = Credit.objects.filter(merchant=merchant, reference__startswith=prefix).count() + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@transaction.atomic
def create_credit(*, merchant, actor, customer, description, total_amount, initial_payment=0, credit_date=None, due_date=None, note=""):
    total_amount = int(total_amount)
    initial_payment = int(initial_payment or 0)
    if total_amount <= 0:
        raise CreditError("Le montant total doit être supérieur à 0.")
    if initial_payment < 0:
        raise CreditError("Le paiement initial ne peut pas être négatif.")
    if initial_payment > total_amount:
        raise CreditError("Le paiement initial ne peut pas dépasser le montant total.")
    if customer.merchant_id != merchant.id:
        raise CreditError("Client invalide.")

    credit = Credit.objects.create(
        merchant=merchant,
        customer=customer,
        reference=generate_credit_reference(merchant),
        description=description.strip(),
        total_amount=total_amount,
        initial_payment=initial_payment,
        paid_amount=0,
        remaining_amount=total_amount,
        credit_date=credit_date or timezone.localdate(),
        due_date=due_date,
        note=(note or "").strip(),
        created_by=actor,
    )
    credit.recompute_amounts(save=True)
    log_action(
        merchant=merchant,
        actor=actor,
        action=AuditLog.Action.CREATE_CREDIT,
        entity=credit,
        summary=f"Crédit {credit.reference} créé pour {customer.display_name} ({total_amount} FCFA)",
        after={
            "reference": credit.reference,
            "customer_id": customer.id,
            "total_amount": total_amount,
            "initial_payment": initial_payment,
            "remaining_amount": credit.remaining_amount,
            "status": credit.status,
        },
    )
    return credit


@transaction.atomic
def add_payment(*, merchant, actor, credit, amount, payment_date=None, method=Payment.Method.CASH, note=""):
    amount = int(amount)
    if credit.merchant_id != merchant.id:
        raise CreditError("Crédit invalide.")
    if credit.is_voided:
        raise CreditError("Impossible d'encaisser un crédit annulé.")
    if credit.remaining_amount <= 0:
        raise CreditError("Ce crédit est déjà réglé.")
    if amount <= 0:
        raise CreditError("Le montant du remboursement doit être supérieur à 0.")
    if amount > credit.remaining_amount:
        raise CreditError("Le remboursement ne peut pas dépasser le reste à payer.")

    payment = Payment.objects.create(
        merchant=merchant,
        credit=credit,
        amount=amount,
        payment_date=payment_date or timezone.localdate(),
        method=method,
        note=(note or "").strip(),
        created_by=actor,
    )
    credit.recompute_amounts(save=True)
    log_action(
        merchant=merchant,
        actor=actor,
        action=AuditLog.Action.ADD_PAYMENT,
        entity=payment,
        summary=f"Remboursement {amount} FCFA sur {credit.reference}",
        after={
            "credit_reference": credit.reference,
            "amount": amount,
            "remaining_amount": credit.remaining_amount,
            "status": credit.status,
        },
    )
    return payment


@transaction.atomic
def void_credit(*, merchant, actor, credit, reason):
    if credit.merchant_id != merchant.id:
        raise CreditError("Crédit invalide.")
    if credit.is_voided:
        return credit
    reason = (reason or "").strip()
    if not reason:
        raise CreditError("Le motif d'annulation est obligatoire.")
    before = {"status": credit.status, "remaining_amount": credit.remaining_amount}
    credit.is_voided = True
    credit.void_reason = reason
    credit.voided_at = timezone.now()
    credit.voided_by = actor
    credit.recompute_status(save=False)
    credit.save(update_fields=["is_voided", "void_reason", "voided_at", "voided_by", "status", "updated_at"])
    log_action(
        merchant=merchant,
        actor=actor,
        action=AuditLog.Action.VOID_CREDIT,
        entity=credit,
        summary=f"Crédit {credit.reference} annulé",
        before=before,
        after={"status": credit.status, "void_reason": reason},
    )
    return credit


@transaction.atomic
def void_payment(*, merchant, actor, payment, reason):
    if payment.merchant_id != merchant.id:
        raise CreditError("Remboursement invalide.")
    if payment.is_voided:
        return payment
    reason = (reason or "").strip()
    if not reason:
        raise CreditError("Le motif d'annulation est obligatoire.")
    credit = payment.credit
    before = {"amount": payment.amount, "credit_remaining": credit.remaining_amount, "credit_status": credit.status}
    payment.is_voided = True
    payment.void_reason = reason
    payment.voided_at = timezone.now()
    payment.voided_by = actor
    payment.save(update_fields=["is_voided", "void_reason", "voided_at", "voided_by"])
    credit.recompute_amounts(save=True)
    log_action(
        merchant=merchant,
        actor=actor,
        action=AuditLog.Action.VOID_PAYMENT,
        entity=payment,
        summary=f"Remboursement {payment.amount} FCFA annulé sur {credit.reference}",
        before=before,
        after={"credit_remaining": credit.remaining_amount, "credit_status": credit.status, "void_reason": reason},
    )
    return payment

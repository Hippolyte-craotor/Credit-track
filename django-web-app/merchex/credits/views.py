from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.models import AuditLog
from audit.services import log_action

from .forms import CreditForm, PaymentForm, VoidForm
from .models import Credit, Payment
from .services import CreditError, add_payment, create_credit, void_credit, void_payment


def _refresh_overdue(queryset):
    today = timezone.localdate()
    queryset.filter(is_voided=False, remaining_amount__gt=0, due_date__lt=today).exclude(status=Credit.Status.OVERDUE).update(status=Credit.Status.OVERDUE)


@login_required
def credit_list(request):
    merchant = request.user.merchant
    _refresh_overdue(Credit.objects.filter(merchant=merchant))
    status = request.GET.get("status", "all")
    q = (request.GET.get("q") or "").strip()
    credits = Credit.objects.filter(merchant=merchant, is_voided=False).select_related("customer")
    if status == "ongoing":
        credits = credits.filter(status=Credit.Status.ONGOING)
    elif status == "partial":
        credits = credits.filter(status=Credit.Status.PARTIALLY_PAID)
    elif status == "paid":
        credits = credits.filter(status=Credit.Status.PAID)
    elif status == "overdue":
        credits = credits.filter(status=Credit.Status.OVERDUE)
    if q:
        credits = credits.filter(Q(customer__display_name__icontains=q) | Q(customer__phone__icontains=q) | Q(reference__icontains=q) | Q(description__icontains=q))
    credits = credits.order_by("-credit_date", "-created_at")
    counts = {
        "all": Credit.objects.filter(merchant=merchant, is_voided=False).count(),
        "ongoing": Credit.objects.filter(merchant=merchant, is_voided=False, status=Credit.Status.ONGOING).count(),
        "partial": Credit.objects.filter(merchant=merchant, is_voided=False, status=Credit.Status.PARTIALLY_PAID).count(),
        "paid": Credit.objects.filter(merchant=merchant, is_voided=False, status=Credit.Status.PAID).count(),
        "overdue": Credit.objects.filter(merchant=merchant, is_voided=False, status=Credit.Status.OVERDUE).count(),
    }
    return render(request, "credits/list.html", {"credits": credits, "status": status, "q": q, "counts": counts})


@login_required
def credit_create(request):
    merchant = request.user.merchant
    initial_customer = request.GET.get("customer")
    form = CreditForm(request.POST or None, merchant=merchant)
    if initial_customer and request.method == "GET":
        form.fields["customer"].initial = initial_customer
    if request.method == "POST" and form.is_valid():
        try:
            credit = create_credit(
                merchant=merchant,
                actor=request.user,
                customer=form.cleaned_data["customer"],
                description=form.cleaned_data["description"],
                total_amount=form.cleaned_data["total_amount"],
                initial_payment=form.cleaned_data["initial_payment"],
                credit_date=form.cleaned_data["credit_date"],
                due_date=form.cleaned_data["due_date"],
                note=form.cleaned_data["note"],
            )
            messages.success(request, f"Crédit {credit.reference} enregistré. Reste à payer: {credit.remaining_amount} FCFA.")
            return redirect("credits:detail", pk=credit.pk)
        except CreditError as e:
            messages.error(request, str(e))
    return render(request, "credits/form.html", {"form": form})


@login_required
def credit_detail(request, pk):
    merchant = request.user.merchant
    credit = get_object_or_404(Credit.objects.select_related("customer"), pk=pk, merchant=merchant)
    credit.recompute_amounts(save=True)
    payments = credit.payments.select_related("created_by").order_by("-payment_date", "-created_at")
    return render(request, "credits/detail.html", {"credit": credit, "payments": payments})


@login_required
def payment_create(request):
    merchant = request.user.merchant
    credit_id = request.GET.get("credit")
    selected_credit = None
    if credit_id:
        selected_credit = Credit.objects.filter(pk=credit_id, merchant=merchant, is_voided=False).first()
    form = PaymentForm(request.POST or None, merchant=merchant, credit=selected_credit)
    if request.method == "POST" and form.is_valid():
        credit = form.cleaned_data["credit"]
        try:
            payment = add_payment(
                merchant=merchant,
                actor=request.user,
                credit=credit,
                amount=form.cleaned_data["amount"],
                payment_date=form.cleaned_data["payment_date"],
                method=form.cleaned_data["method"],
                note=form.cleaned_data["note"],
            )
            messages.success(request, f"Remboursement de {payment.amount} FCFA enregistré.")
            return redirect("credits:detail", pk=credit.pk)
        except CreditError as e:
            messages.error(request, str(e))
    return render(request, "credits/payment_form.html", {"form": form, "selected_credit": selected_credit})


@login_required
def payment_create_for_credit(request, pk):
    merchant = request.user.merchant
    credit = get_object_or_404(Credit, pk=pk, merchant=merchant, is_voided=False)
    return redirect(f"/dettes/encaisser/?credit={credit.pk}")


@login_required
def credit_void(request, pk):
    merchant = request.user.merchant
    credit = get_object_or_404(Credit, pk=pk, merchant=merchant)
    form = VoidForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            void_credit(merchant=merchant, actor=request.user, credit=credit, reason=form.cleaned_data["reason"])
            messages.success(request, "Crédit annulé. L'historique a été conservé.")
            return redirect("credits:detail", pk=credit.pk)
        except CreditError as e:
            messages.error(request, str(e))
    return render(request, "credits/void.html", {"form": form, "object": credit, "type": "crédit"})


@login_required
def payment_void(request, pk):
    merchant = request.user.merchant
    payment = get_object_or_404(Payment.objects.select_related("credit"), pk=pk, merchant=merchant)
    form = VoidForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            void_payment(merchant=merchant, actor=request.user, payment=payment, reason=form.cleaned_data["reason"])
            messages.success(request, "Remboursement annulé. Le solde a été recalculé.")
            return redirect("credits:detail", pk=payment.credit_id)
        except CreditError as e:
            messages.error(request, str(e))
    return render(request, "credits/void.html", {"form": form, "object": payment, "type": "remboursement"})

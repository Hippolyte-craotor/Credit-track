from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import log_action
from credits.models import Credit

from .forms import CustomerForm
from .models import Customer


@login_required
def customer_list(request):
    q = (request.GET.get("q") or "").strip()
    customers = Customer.objects.filter(merchant=request.user.merchant, is_active=True)
    if q:
        customers = customers.filter(Q(display_name__icontains=q) | Q(phone__icontains=q))
    customers = customers.order_by("display_name")
    for c in customers:
        c.remaining_total = (
            c.credits.filter(merchant=request.user.merchant, is_voided=False)
            .exclude(status=Credit.Status.PAID)
            .aggregate(total=Sum("remaining_amount"))["total"]
            or 0
        )
    return render(request, "customers/list.html", {"customers": customers, "q": q})


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save(commit=False)
        customer.merchant = request.user.merchant
        customer.save()
        log_action(
            merchant=request.user.merchant,
            actor=request.user,
            action=AuditLog.Action.CREATE_CUSTOMER,
            entity=customer,
            summary=f"Client créé: {customer.display_name}",
            after={"display_name": customer.display_name, "phone": customer.phone},
        )
        messages.success(request, "Client ajouté avec succès.")
        next_url = request.GET.get("next")
        return redirect(next_url or "customers:detail", pk=customer.pk)
    return render(request, "customers/form.html", {"form": form, "title": "Ajouter un client"})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk, merchant=request.user.merchant)
    credits = customer.credits.filter(merchant=request.user.merchant).order_by("-credit_date", "-created_at")
    total_remaining = credits.filter(is_voided=False).exclude(status=Credit.Status.PAID).aggregate(total=Sum("remaining_amount"))["total"] or 0
    return render(request, "customers/detail.html", {"customer": customer, "credits": credits, "total_remaining": total_remaining})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, merchant=request.user.merchant)
    before = {"display_name": customer.display_name, "phone": customer.phone, "address": customer.address}
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        log_action(
            merchant=request.user.merchant,
            actor=request.user,
            action=AuditLog.Action.UPDATE_CUSTOMER,
            entity=customer,
            summary=f"Client modifié: {customer.display_name}",
            before=before,
            after={"display_name": customer.display_name, "phone": customer.phone, "address": customer.address},
        )
        messages.success(request, "Client modifié.")
        return redirect("customers:detail", pk=customer.pk)
    return render(request, "customers/form.html", {"form": form, "title": "Modifier le client", "customer": customer})

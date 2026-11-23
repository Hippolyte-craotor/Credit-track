from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .forms import OrderCreateForm, OrderStatusForm
from .models import Order


@login_required
def order_create(request, product_pk):
    if request.user.role != "ACHETEUR" and not request.user.is_superuser:
        messages.error(request, "Seuls les acheteurs peuvent passer des commandes.")
        return redirect("products:detail", pk=product_pk)

    product = get_object_or_404(Product, pk=product_pk, is_available=True)
    if product.quantity < 1:
        messages.error(request, "Ce produit n'est plus disponible.")
        return redirect("products:detail", pk=product_pk)
    if product.producer == request.user:
        messages.error(request, "Vous ne pouvez pas commander votre propre produit.")
        return redirect("products:detail", pk=product_pk)

    if request.method == "POST":
        form = OrderCreateForm(request.POST, product=product)
        if form.is_valid():
            try:
                with transaction.atomic():
                    locked_product = Product.objects.select_for_update().get(pk=product.pk)
                    qty = form.cleaned_data["quantity"]
                    if qty > locked_product.quantity or not locked_product.is_available:
                        messages.error(request, "Stock insuffisant pour cette commande.")
                        return redirect("products:detail", pk=product_pk)
                    order = form.save(commit=False)
                    order.buyer = request.user
                    order.product = locked_product
                    order.producer = locked_product.producer
                    order.unit_price = locked_product.price
                    order.total_price = (Decimal(qty) * locked_product.price).quantize(Decimal("0.01"))
                    order.save()
                    locked_product.quantity -= qty
                    if locked_product.quantity == 0:
                        locked_product.is_available = False
                    locked_product.save(update_fields=["quantity", "is_available", "updated_at"])
                messages.success(request, "Commande passée avec succès.")
                return redirect("orders:detail", pk=order.pk)
            except Exception:
                messages.error(request, "Une erreur est survenue lors de la commande. Veuillez réessayer.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        initial = {"delivery_address": request.user.address}
        form = OrderCreateForm(initial=initial, product=product)

    return render(request, "orders/order_form.html", {"form": form, "product": product})


@login_required
def order_list(request):
    user = request.user
    qs = Order.objects.select_related("product", "buyer", "producer", "transporter")
    if user.is_superuser or user.role == "ADMIN":
        orders = qs
    elif user.role == "PRODUCTEUR":
        orders = qs.filter(producer=user)
    elif user.role == "ACHETEUR":
        orders = qs.filter(buyer=user)
    elif user.role == "TRANSPORTEUR":
        orders = qs.filter(Q(transporter=user) | Q(status__in=[Order.Status.CONFIRMEE, Order.Status.EN_LIVRAISON]))
    else:
        orders = qs.none()
    status = request.GET.get("status", "").strip()
    if status:
        orders = orders.filter(status=status)
    return render(request, "orders/order_list.html", {"orders": orders, "status_filter": status, "statuses": Order.Status.choices})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("product", "buyer", "producer", "transporter"), pk=pk)
    user = request.user
    allowed = (
        user.is_superuser
        or user.role == "ADMIN"
        or order.buyer_id == user.id
        or order.producer_id == user.id
        or order.transporter_id == user.id
        or (user.role == "TRANSPORTEUR" and order.status in [Order.Status.CONFIRMEE, Order.Status.EN_LIVRAISON])
    )
    if not allowed:
        messages.error(request, "Vous n'avez pas accès à cette commande.")
        return redirect("orders:list")

    status_form = None
    can_update = False
    if user.is_superuser or user.role == "ADMIN" or order.producer_id == user.id or order.buyer_id == user.id or user.role == "TRANSPORTEUR":
        status_form = OrderStatusForm(instance=order, user=user)
        can_update = any(choice[0] for choice in status_form.fields["status"].choices)
    return render(request, "orders/order_detail.html", {"order": order, "status_form": status_form, "can_update_status": can_update})


@login_required
def order_update_status(request, pk):
    order = get_object_or_404(Order.objects.select_related("product"), pk=pk)
    user = request.user
    if request.method != "POST":
        return redirect("orders:detail", pk=pk)
    form = OrderStatusForm(request.POST, instance=order, user=user)
    if not form.is_valid():
        messages.error(request, "Statut invalide.")
        return redirect("orders:detail", pk=pk)

    new_status = form.cleaned_data["status"]
    if not new_status:
        messages.error(request, "Veuillez choisir un statut.")
        return redirect("orders:detail", pk=pk)
    if not order.can_transition_to(new_status, user):
        messages.error(request, "Vous n'êtes pas autorisé à effectuer cette transition.")
        return redirect("orders:detail", pk=pk)

    with transaction.atomic():
        locked_order = Order.objects.select_for_update().select_related("product").get(pk=pk)
        old_status = locked_order.status
        if old_status == new_status:
            return redirect("orders:detail", pk=pk)
        if new_status == Order.Status.ANNULEE and old_status != Order.Status.ANNULEE:
            product = Product.objects.select_for_update().get(pk=locked_order.product_id)
            product.quantity += locked_order.quantity
            if product.quantity > 0:
                product.is_available = True
            product.save(update_fields=["quantity", "is_available", "updated_at"])
        if user.role == "TRANSPORTEUR" and locked_order.transporter_id is None and new_status in [Order.Status.EN_LIVRAISON, Order.Status.LIVREE]:
            locked_order.transporter = user
        locked_order.status = new_status
        locked_order.save()
    messages.success(request, "Statut de la commande mis à jour.")
    return redirect("orders:detail", pk=pk)

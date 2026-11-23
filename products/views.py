from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm
from .models import Product


def home(request):
    products = Product.objects.filter(is_available=True, quantity__gt=0).select_related("producer")[:8]
    stats = {
        "products": Product.objects.filter(is_available=True).count(),
        "producers": Product.objects.values("producer").distinct().count(),
    }
    return render(request, "home.html", {"products": products, "stats": stats})


def product_list(request):
    products = Product.objects.filter(is_available=True).select_related("producer")
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    region = request.GET.get("region", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(producer__username__icontains=q))
    if category:
        products = products.filter(category=category)
    if region:
        products = products.filter(location__icontains=region)
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    context = {
        "products": products,
        "q": q,
        "category": category,
        "region": region,
        "min_price": min_price,
        "max_price": max_price,
        "categories": Product.Category.choices,
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("producer"), pk=pk)
    return render(request, "products/product_detail.html", {"product": product})


def _producer_required(request):
    if not request.user.is_authenticated:
        return False
    return request.user.role == "PRODUCTEUR" or request.user.is_superuser


@login_required
def product_create(request):
    if request.user.role != "PRODUCTEUR" and not request.user.is_superuser:
        messages.error(request, "Seuls les producteurs peuvent publier des produits.")
        return redirect("dashboard:home")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.producer = request.user
            product.save()
            messages.success(request, "Produit publié avec succès.")
            return redirect("products:detail", pk=product.pk)
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ProductForm()
    return render(request, "products/product_form.html", {"form": form, "title": "Publier un produit"})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.producer != request.user and not request.user.is_superuser:
        messages.error(request, "Vous ne pouvez pas modifier ce produit.")
        return redirect("products:detail", pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit mis à jour.")
            return redirect("products:detail", pk=product.pk)
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ProductForm(instance=product)
    return render(request, "products/product_form.html", {"form": form, "title": "Modifier le produit", "product": product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.producer != request.user and not request.user.is_superuser:
        messages.error(request, "Vous ne pouvez pas supprimer ce produit.")
        return redirect("products:detail", pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Produit supprimé.")
        return redirect("dashboard:home")
    return render(request, "products/product_confirm_delete.html", {"product": product})

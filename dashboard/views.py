from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from accounts.models import User
from orders.models import Order
from products.models import Product


@login_required
def home(request):
    user = request.user
    context = {"active_page": "dashboard"}

    if user.is_superuser or user.role == User.Roles.ADMIN:
        context.update(
            {
                "total_users": User.objects.count(),
                "total_producers": User.objects.filter(role=User.Roles.PRODUCTEUR).count(),
                "total_buyers": User.objects.filter(role=User.Roles.ACHETEUR).count(),
                "total_transporters": User.objects.filter(role=User.Roles.TRANSPORTEUR).count(),
                "total_products": Product.objects.count(),
                "available_products": Product.objects.filter(is_available=True).count(),
                "total_orders": Order.objects.count(),
                "pending_orders": Order.objects.filter(status=Order.Status.EN_ATTENTE).count(),
                "revenue": Order.objects.exclude(status=Order.Status.ANNULEE).aggregate(total=Sum("total_price"))["total"] or 0,
                "recent_orders": Order.objects.select_related("product", "buyer", "producer")[:8],
                "recent_users": User.objects.order_by("-date_joined")[:8],
                "orders_by_status": Order.objects.values("status").annotate(count=Count("id")).order_by("status"),
            }
        )
        return render(request, "dashboard/admin_dashboard.html", context)

    if user.role == User.Roles.PRODUCTEUR:
        my_products = Product.objects.filter(producer=user)
        my_orders = Order.objects.filter(producer=user).select_related("product", "buyer")
        context.update(
            {
                "my_products": my_products[:8],
                "my_products_count": my_products.count(),
                "active_products_count": my_products.filter(is_available=True).count(),
                "received_orders": my_orders[:8],
                "pending_orders_count": my_orders.filter(status=Order.Status.EN_ATTENTE).count(),
                "total_sales": my_orders.exclude(status=Order.Status.ANNULEE).aggregate(total=Sum("total_price"))["total"] or 0,
            }
        )
        return render(request, "dashboard/producer_dashboard.html", context)

    if user.role == User.Roles.ACHETEUR:
        my_orders = Order.objects.filter(buyer=user).select_related("product", "producer")
        context.update(
            {
                "my_orders": my_orders[:8],
                "orders_count": my_orders.count(),
                "pending_orders_count": my_orders.filter(status=Order.Status.EN_ATTENTE).count(),
                "total_spent": my_orders.exclude(status=Order.Status.ANNULEE).aggregate(total=Sum("total_price"))["total"] or 0,
            }
        )
        return render(request, "dashboard/buyer_dashboard.html", context)

    if user.role == User.Roles.TRANSPORTEUR:
        deliveries = Order.objects.filter(transporter=user).select_related("product", "buyer", "producer")
        available = Order.objects.filter(status__in=[Order.Status.CONFIRMEE, Order.Status.EN_LIVRAISON]).select_related("product", "buyer", "producer")
        context.update(
            {
                "deliveries": deliveries[:8],
                "deliveries_count": deliveries.count(),
                "in_delivery_count": deliveries.filter(status=Order.Status.EN_LIVRAISON).count(),
                "available_deliveries": available[:8],
            }
        )
        return render(request, "dashboard/transporter_dashboard.html", context)

    return render(request, "dashboard/buyer_dashboard.html", context)

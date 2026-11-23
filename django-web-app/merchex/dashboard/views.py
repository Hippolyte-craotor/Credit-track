from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from audit.models import AuditLog
from credits.models import Credit
from customers.models import Customer


@login_required
def index(request):
    merchant = request.user.merchant
    today = timezone.localdate()
    Credit.objects.filter(merchant=merchant, is_voided=False, remaining_amount__gt=0, due_date__lt=today).exclude(status=Credit.Status.OVERDUE).update(status=Credit.Status.OVERDUE)

    credits = Credit.objects.filter(merchant=merchant, is_voided=False)
    totals = credits.aggregate(
        total_credits=Sum("total_amount"),
        total_paid=Sum("paid_amount"),
        total_remaining=Sum("remaining_amount"),
    )
    overdue_qs = credits.filter(status=Credit.Status.OVERDUE)
    overdue_count = overdue_qs.count()
    clients_with_debt = Customer.objects.filter(merchant=merchant, is_active=True, credits__is_voided=False, credits__remaining_amount__gt=0).distinct().count()
    recent_operations = AuditLog.objects.filter(merchant=merchant).select_related("actor")[:8]
    overdue_top = overdue_qs.select_related("customer").order_by("due_date")[:5]

    context = {
        "total_credits": totals["total_credits"] or 0,
        "total_paid": totals["total_paid"] or 0,
        "total_remaining": totals["total_remaining"] or 0,
        "clients_with_debt": clients_with_debt,
        "overdue_count": overdue_count,
        "recent_operations": recent_operations,
        "overdue_top": overdue_top,
    }
    return render(request, "dashboard/index.html", context)

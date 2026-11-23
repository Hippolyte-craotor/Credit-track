import io
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from audit.models import AuditLog
from credits.models import Credit
from customers.models import Customer


def _date_range(request):
    start = request.GET.get("from")
    end = request.GET.get("to")
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
    except ValueError:
        start_date = None
    try:
        end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None
    except ValueError:
        end_date = None
    return start_date, end_date


@login_required
def history(request):
    merchant = request.user.merchant
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("type") or "").strip()
    logs = AuditLog.objects.filter(merchant=merchant).select_related("actor")
    if q:
        logs = logs.filter(Q(summary__icontains=q) | Q(entity_id__icontains=q))
    if action:
        logs = logs.filter(action=action)
    start, end = _date_range(request)
    if start:
        logs = logs.filter(created_at__date__gte=start)
    if end:
        logs = logs.filter(created_at__date__lte=end)
    logs = logs[:200]
    return render(request, "reports/history.html", {"logs": logs, "q": q, "type": action, "actions": AuditLog.Action.choices, "start": start, "end": end})


@login_required
def reports_index(request):
    merchant = request.user.merchant
    start, end = _date_range(request)
    credits = Credit.objects.filter(merchant=merchant, is_voided=False)
    if start:
        credits = credits.filter(credit_date__gte=start)
    if end:
        credits = credits.filter(credit_date__lte=end)
    totals = credits.aggregate(total_credits=Sum("total_amount"), total_paid=Sum("paid_amount"), total_remaining=Sum("remaining_amount"))
    top_debtors = (
        Customer.objects.filter(merchant=merchant, is_active=True, credits__is_voided=False)
        .annotate(outstanding=Sum("credits__remaining_amount"))
        .filter(outstanding__gt=0)
        .order_by("-outstanding")[:10]
    )
    overdue = Credit.objects.filter(merchant=merchant, is_voided=False, status=Credit.Status.OVERDUE).select_related("customer").order_by("due_date")
    context = {
        "total_credits": totals["total_credits"] or 0,
        "total_paid": totals["total_paid"] or 0,
        "total_remaining": totals["total_remaining"] or 0,
        "top_debtors": top_debtors,
        "overdue": overdue,
        "start": start,
        "end": end,
    }
    return render(request, "reports/index.html", context)


@login_required
def export_excel(request):
    merchant = request.user.merchant
    start, end = _date_range(request)
    credits = Credit.objects.filter(merchant=merchant, is_voided=False).select_related("customer").order_by("-credit_date")
    if start:
        credits = credits.filter(credit_date__gte=start)
    if end:
        credits = credits.filter(credit_date__lte=end)
    try:
        from openpyxl import Workbook
    except Exception:
        # Fallback CSV
        buffer = io.StringIO()
        buffer.write("Reference;Client;Date;Total FCFA;Paye FCFA;Reste FCFA;Statut\n")
        for c in credits:
            buffer.write(f"{c.reference};{c.customer.display_name};{c.credit_date};{c.total_amount};{c.paid_amount};{c.remaining_amount};{c.get_status_display()}\n")
        resp = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="credittrack-rapport.csv"'
        return resp

    wb = Workbook()
    ws = wb.active
    ws.title = "Rapport"
    ws.append(["Référence", "Client", "Téléphone", "Date", "Description", "Total FCFA", "Payé FCFA", "Reste FCFA", "Statut", "Échéance"])
    for c in credits:
        ws.append([c.reference, c.customer.display_name, c.customer.phone, c.credit_date.isoformat(), c.description, c.total_amount, c.paid_amount, c.remaining_amount, c.get_status_display(), c.due_date.isoformat() if c.due_date else ""])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    resp = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = 'attachment; filename="credittrack-rapport.xlsx"'
    return resp


@login_required
def export_pdf(request):
    merchant = request.user.merchant
    start, end = _date_range(request)
    credits = Credit.objects.filter(merchant=merchant, is_voided=False).select_related("customer").order_by("-credit_date")
    if start:
        credits = credits.filter(credit_date__gte=start)
    if end:
        credits = credits.filter(credit_date__lte=end)
    totals = credits.aggregate(total_credits=Sum("total_amount"), total_paid=Sum("paid_amount"), total_remaining=Sum("remaining_amount"))
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        # Fallback printable HTML
        return render(request, "reports/export_pdf_fallback.html", {"credits": credits, "totals": totals, "start": start, "end": end})

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), margin=24)
    styles = getSampleStyleSheet()
    elements = [Paragraph("CreditTrack - Rapport des dettes", styles["Title"])]
    period = f"Période: {start or '...'} au {end or '...'}"
    elements.append(Paragraph(period, styles["Normal"]))
    elements.append(Paragraph(f"Total crédits: {totals['total_credits'] or 0} FCFA | Total remboursé: {totals['total_paid'] or 0} FCFA | Reste: {totals['total_remaining'] or 0} FCFA", styles["Normal"]))
    elements.append(Spacer(1, 12))
    data = [["Référence", "Client", "Date", "Total", "Payé", "Reste", "Statut"]]
    for c in credits[:500]:
        data.append([c.reference, c.customer.display_name[:24], c.credit_date.strftime("%d/%m/%Y"), str(c.total_amount), str(c.paid_amount), str(c.remaining_amount), c.get_status_display()])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#184430')), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f3f4f6')])]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="credittrack-rapport.pdf"'
    return resp

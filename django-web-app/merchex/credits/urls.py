from django.urls import path
from . import views

app_name = "credits"

urlpatterns = [
    path("", views.credit_list, name="list"),
    path("nouveau/", views.credit_create, name="create"),
    path("<int:pk>/", views.credit_detail, name="detail"),
    path("<int:pk>/encaisser/", views.payment_create_for_credit, name="payment_for_credit"),
    path("encaisser/", views.payment_create, name="payment_create"),
    path("<int:pk>/annuler/", views.credit_void, name="void"),
    path("paiements/<int:pk>/annuler/", views.payment_void, name="payment_void"),
]

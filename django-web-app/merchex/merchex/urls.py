from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dashboard:index", permanent=False)),
    path("comptes/", include("accounts.urls")),
    path("tableau-de-bord/", include("dashboard.urls")),
    path("clients/", include("customers.urls")),
    path("dettes/", include("credits.urls")),
    path("rapports/", include("reports.urls")),
    # Legacy placeholder routes kept to avoid breaking old links during transition.
    path("hello/", RedirectView.as_view(pattern_name="dashboard:index", permanent=False)),
]

from django.urls import path

from .views import PainelView, RegistrarEventoView, TendenciasView

urlpatterns = [
    path("analytics/", RegistrarEventoView.as_view(), name="analytics-evento"),
    path("analytics/trending/", TendenciasView.as_view(), name="analytics-tendencias"),
    path("analytics/dashboard/", PainelView.as_view(), name="analytics-painel"),
]

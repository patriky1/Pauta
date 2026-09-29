from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import FavoritoViewSet, HistoricoViewSet, SeguirView

router = DefaultRouter()
router.register("favorites", FavoritoViewSet, basename="favorito")
router.register("history", HistoricoViewSet, basename="historico")

urlpatterns = router.urls + [
    path("follow/<str:tipo>/", SeguirView.as_view(), name="seguir"),
]

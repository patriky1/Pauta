from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AnuncioViewSet,
    BuscaView,
    CoberturaAoVivoViewSet,
    NoticiaAdminViewSet,
    NoticiaViewSet,
    VideoViewSet,
)

router = DefaultRouter()
router.register("news", NoticiaViewSet, basename="noticia")
router.register("admin/news", NoticiaAdminViewSet, basename="admin-noticia")
router.register("live", CoberturaAoVivoViewSet, basename="cobertura")
router.register("videos", VideoViewSet, basename="video")
router.register("ads", AnuncioViewSet, basename="anuncio")

urlpatterns = router.urls + [
    path("search/", BuscaView.as_view(), name="busca"),
]

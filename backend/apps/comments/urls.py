from rest_framework.routers import DefaultRouter

from .views import ComentarioViewSet, DenunciaViewSet

router = DefaultRouter()
router.register("comments", ComentarioViewSet, basename="comentario")
router.register("reports", DenunciaViewSet, basename="denuncia")

urlpatterns = router.urls

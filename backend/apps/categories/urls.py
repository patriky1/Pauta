from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, TagViewSet

router = DefaultRouter()
router.register("categories", CategoriaViewSet, basename="categoria")
router.register("tags", TagViewSet, basename="tag")

urlpatterns = router.urls

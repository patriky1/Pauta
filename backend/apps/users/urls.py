from rest_framework.routers import DefaultRouter

from .views import AutorViewSet, UsuarioAdminViewSet

router = DefaultRouter()
router.register("authors", AutorViewSet, basename="autor")
router.register("admin/users", UsuarioAdminViewSet, basename="admin-usuario")

urlpatterns = router.urls

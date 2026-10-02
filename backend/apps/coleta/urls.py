from rest_framework.routers import DefaultRouter

from .views import (
    ExecucaoColetaViewSet,
    FonteNoticiaViewSet,
    MapeamentoCategoriaViewSet,
    RegraCategorizacaoViewSet,
)

router = DefaultRouter()
router.register("coleta/fontes", FonteNoticiaViewSet, basename="coleta-fonte")
router.register("coleta/execucoes", ExecucaoColetaViewSet, basename="coleta-execucao")
router.register("coleta/mapeamentos", MapeamentoCategoriaViewSet, basename="coleta-mapeamento")
router.register("coleta/regras", RegraCategorizacaoViewSet, basename="coleta-regra")

urlpatterns = router.urls

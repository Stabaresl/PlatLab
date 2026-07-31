from rest_framework.routers import SimpleRouter

from modules.gamification.presentation.views import (
    CosmeticoDesbloqueadoViewSet,
    GamificationViewSet,
    TituloDesbloqueadoViewSet,
)

router = SimpleRouter()
router.register(r"cosmeticos", CosmeticoDesbloqueadoViewSet, basename="gamification-cosmetico")
router.register(r"titulos", TituloDesbloqueadoViewSet, basename="gamification-titulo")
router.register(r"", GamificationViewSet, basename="gamification")

urlpatterns = router.urls

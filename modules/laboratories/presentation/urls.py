from rest_framework.routers import SimpleRouter

from modules.laboratories.presentation.views import LaboratorioViewSet

router = SimpleRouter()
router.register(r"", LaboratorioViewSet, basename="laboratorio")

urlpatterns = router.urls

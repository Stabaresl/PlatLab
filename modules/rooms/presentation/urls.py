from rest_framework.routers import SimpleRouter

from modules.rooms.presentation.views import SalaViewSet

router = SimpleRouter()
router.register(r"", SalaViewSet, basename="sala")

urlpatterns = router.urls

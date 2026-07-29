from rest_framework.routers import SimpleRouter

from modules.users.presentation.views import UserViewSet

router = SimpleRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = router.urls

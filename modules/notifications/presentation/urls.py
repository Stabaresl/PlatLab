from rest_framework.routers import SimpleRouter

from modules.notifications.presentation.views import NotificationViewSet

router = SimpleRouter()
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = router.urls

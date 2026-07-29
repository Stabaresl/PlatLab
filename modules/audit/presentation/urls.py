from rest_framework.routers import SimpleRouter

from modules.audit.presentation.views import AuditViewSet

router = SimpleRouter()
router.register(r"", AuditViewSet, basename="audit")

urlpatterns = router.urls

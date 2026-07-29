from rest_framework.routers import SimpleRouter

from modules.reports.presentation.views import ReportViewSet

router = SimpleRouter()
router.register(r"", ReportViewSet, basename="report")

urlpatterns = router.urls

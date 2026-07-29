from rest_framework.routers import SimpleRouter

from modules.assignments.presentation.views import AssignmentViewSet, InvitationViewSet

router = SimpleRouter()
router.register(r"invitations", InvitationViewSet, basename="invitation")
router.register(r"", AssignmentViewSet, basename="assignment")

urlpatterns = router.urls

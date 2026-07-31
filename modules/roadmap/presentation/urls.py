from rest_framework.routers import SimpleRouter

from modules.roadmap.presentation.views import NodoRoadmapViewSet, RoadmapViewSet

router = SimpleRouter()
router.register(r"nodos", NodoRoadmapViewSet, basename="roadmap-nodo")
router.register(r"", RoadmapViewSet, basename="roadmap")

urlpatterns = router.urls

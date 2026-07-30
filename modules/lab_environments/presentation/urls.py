from django.urls import path

from modules.lab_environments.presentation.views import (
    EntornoStartView,
    EntornoStatusView,
    EntornoStopView,
)

urlpatterns = [
    path(
        "<str:assignment_id>/sections/<str:section_id>/start/",
        EntornoStartView.as_view(),
        name="lab-environment-start",
    ),
    path(
        "<str:assignment_id>/sections/<str:section_id>/status/",
        EntornoStatusView.as_view(),
        name="lab-environment-status",
    ),
    path("<str:entorno_id>/stop/", EntornoStopView.as_view(), name="lab-environment-stop"),
]

from django.urls import path

from modules.progress.presentation.views import (
    ContenidoSeccionView,
    ExamSubmissionView,
    FlagValidationView,
    HintView,
    HistoryView,
)

urlpatterns = [
    path(
        "<str:assignment_id>/sections/<str:section_id>/flag/",
        FlagValidationView.as_view(),
        name="progress-flag",
    ),
    path(
        "<str:assignment_id>/sections/<str:section_id>/hint/",
        HintView.as_view(),
        name="progress-hint",
    ),
    path(
        "<str:assignment_id>/sections/<str:section_id>/",
        ContenidoSeccionView.as_view(),
        name="progress-section-content",
    ),
    path("<str:assignment_id>/exam/", ExamSubmissionView.as_view(), name="progress-exam"),
    path("<str:assignment_id>/history/", HistoryView.as_view(), name="progress-history"),
]

from django.urls import path

from modules.progress.presentation.views import (
    ContenidoSeccionView,
    ExamStartView,
    ExamSubmissionView,
    FlagValidationView,
    HintView,
    HistoryView,
    ProgresoOverviewView,
    SectionCompletionView,
)

urlpatterns = [
    path(
        "<str:assignment_id>/sections/<str:section_id>/flag/",
        FlagValidationView.as_view(),
        name="progress-flag",
    ),
    path(
        "<str:assignment_id>/sections/<str:section_id>/complete/",
        SectionCompletionView.as_view(),
        name="progress-section-complete",
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
    path("<str:assignment_id>/exam/iniciar/", ExamStartView.as_view(), name="progress-exam-start"),
    path("<str:assignment_id>/exam/", ExamSubmissionView.as_view(), name="progress-exam"),
    path("<str:assignment_id>/history/", HistoryView.as_view(), name="progress-history"),
    path("<str:assignment_id>/", ProgresoOverviewView.as_view(), name="progress-overview"),
]

"""
URL configuration for PlatLab project.

Each module registers its own routes via the shared router pattern.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

    # Module routes
    path('api/v1/auth/', include('modules.authentication.presentation.urls')),
    path('api/v1/users/', include('modules.users.presentation.urls')),
    path('api/v1/laboratories/', include('modules.laboratories.presentation.urls')),
    path('api/v1/assignments/', include('modules.assignments.presentation.urls')),
    path('api/v1/progress/', include('modules.progress.presentation.urls')),
    path('api/v1/reports/', include('modules.reports.presentation.urls')),
    path('api/v1/notifications/', include('modules.notifications.presentation.urls')),
    path('api/v1/audit/', include('modules.audit.presentation.urls')),
]

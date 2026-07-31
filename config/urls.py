"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny

from config.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', HealthCheckView.as_view(), name='health'),
    path(
        'api/v1/schema/',
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name='schema',
    ),
    path(
        'api/v1/docs/',
        SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]),
        name='docs',
    ),
    path('api/v1/auth/', include('modules.authentication.presentation.urls')),
    path('api/v1/laboratories/', include('modules.laboratories.presentation.urls')),
    path('api/v1/progress/', include('modules.progress.presentation.urls')),
    path('api/v1/assignments/', include('modules.assignments.presentation.urls')),
    path('api/v1/users/', include('modules.users.presentation.urls')),
    path('api/v1/reports/', include('modules.reports.presentation.urls')),
    path('api/v1/notifications/', include('modules.notifications.presentation.urls')),
    path('api/v1/audit/', include('modules.audit.presentation.urls')),
    path('api/v1/lab-environments/', include('modules.lab_environments.presentation.urls')),
    path('api/v1/roadmap/', include('modules.roadmap.presentation.urls')),
    path('api/v1/gamification/', include('modules.gamification.presentation.urls')),
]

# Adjuntos de reportes y Dockerfiles subidos por instructores (MEDIA_ROOT)
# — solo en dev; en producción los sirve el proveedor de almacenamiento
# (S3/MinIO, RNF-08.1) directamente, no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

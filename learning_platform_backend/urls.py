from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),

    path("api/users/", include("users.urls")),
    path("api/courses/", include("courses.urls")),
    path("api/enrollments/", include("enrollments.urls")),
    path("api/feedback/", include("feedback.urls")),
]

# Media en desarrollo: el helper static() solo funciona en DEBUG y con prefijo local (/media/)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

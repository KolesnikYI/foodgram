from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    re_path(r'^auth/', include('djoser.urls')),
]
if settings.DEBUG:
    import debug_toolbar  # type: ignore

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)

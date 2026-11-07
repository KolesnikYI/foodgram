import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from dotenv import load_dotenv

from recipes.views import short_link_redirect


load_dotenv()
POSTMAN = os.getenv('POSTMAN', 'True') == 'True'
api_version = '' if POSTMAN else 'v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('s/<str:short_code>/', short_link_redirect, name='short-link'),
    path(f'api/{api_version}', include('api.urls')),
]
if settings.DEBUG:
    import debug_toolbar  # type: ignore

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

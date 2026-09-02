import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from dotenv import load_dotenv


load_dotenv()
POSTMAN = os.getenv('POSTMAN', 'True') == 'True'
api_version = '' if POSTMAN else 'v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'api/{api_version}', include('api.urls')),
]
if settings.DEBUG:
    import debug_toolbar  # type: ignore

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)

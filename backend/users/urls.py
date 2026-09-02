from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet


router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')

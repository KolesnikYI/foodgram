from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import permissions
from users.serializers import CustomUserSerializer


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet пользователя - в разработке."""

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

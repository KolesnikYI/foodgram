import base64

from config.constants import LAST_ELEM
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор для работы с изображениями."""

    def to_internal_value(self, data: str | ContentFile) -> None:
        """Метод для сериализации изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[LAST_ELEM]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Cериализатор для модели пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    # is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            # 'is_subscribed',
            'avatar',
        )

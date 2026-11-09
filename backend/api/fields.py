import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from config.constants import LAST_ELEM


class Base64ImageField(serializers.ImageField):
    """Поле для приёма изображения в формате base64."""

    def to_internal_value(self, data: str | ContentFile) -> ContentFile:
        """Декодировать base64-строку в файл изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = header.split('/')[LAST_ELEM]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Модель пользователя foodgram."""

    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='user_avatars/',
        blank=True,
        null=True,
    )

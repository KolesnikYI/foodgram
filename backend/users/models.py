from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from config.constants import MAX_LENGTH
from recipes.models import TimeStampedModel


class FoodgramUser(AbstractUser):
    """Модель пользователя foodgram."""

    email = models.EmailField(
        verbose_name='e-mail',
        max_length=MAX_LENGTH,
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH,
        blank=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH,
        blank=False,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users_avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']  # noqa: RUF012

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        """Вернуть e-mail пользователя."""
        return self.email


class Subscription(TimeStampedModel):
    """Подписка пользователя на автора."""

    user = models.ForeignKey(
        to=FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        to=FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        """Мета-класс модели."""

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                condition=~Q(user=F('author')),
                name='prevent_self_subscription',
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self) -> str:
        """Вернуть строковое представление подписки."""
        return f'{self.user} -> {self.author}'

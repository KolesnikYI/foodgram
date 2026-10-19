from django.db import models


class TimeStampedModel(models.Model):
    """Абстрактная модель с метками времени создания и изменения."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )
    altered_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Изменено',
    )

    class Meta:
        """Мета-класс модели."""

        abstract = True

from collections.abc import Iterable

from config.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    INGREDIENT_AMOUNT_MAX,
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    SHORT_CODE_LENGTH,
    SHORT_CODE_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string

from api.models import TimeStampedModel


class Tag(TimeStampedModel):
    """Модель тега."""

    name = models.CharField(max_length=TAG_NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(max_length=TAG_SLUG_MAX_LENGTH, unique=True)

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        """Вернуть название тега."""
        return self.name


class Ingredient(TimeStampedModel):
    """Модель ингредиента."""

    name = models.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        """Мета-класс модели."""

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_measurement_unit',
            ),
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        """Вернуть название ингредиента."""
        return self.name


class Recipe(TimeStampedModel):
    """Модель рецепта."""

    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH)
    image = models.ImageField(upload_to='recipes/images/')
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(COOKING_TIME_MIN),
            MaxValueValidator(COOKING_TIME_MAX),
        ],
    )
    tags = models.ManyToManyField(to=Tag, related_name='recipes')
    ingredients: models.ManyToManyField = models.ManyToManyField(
        to=Ingredient,
        related_name='recipes',
        through='RecipeIngredient',
    )
    short_code = models.CharField(
        max_length=SHORT_CODE_MAX_LENGTH,
        unique=True,
        blank=True,
    )

    class Meta:
        """Мета-класс модели."""

        ordering = ('-created_at',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        """Вернуть название рецепта."""
        return self.name

    def save(  # type: ignore[override]
        self,
        *,
        force_insert: bool = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        """Сохранить рецепт, сгенерировав short_code при первом сохранении."""
        if not self.short_code:
            self.short_code = self._generate_unique_short_code()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @classmethod
    def _generate_unique_short_code(cls) -> str:
        """Сгенерировать уникальный короткий код рецепта."""
        while True:
            short_code = get_random_string(length=SHORT_CODE_LENGTH)
            if not cls.objects.filter(short_code=short_code).exists():
                return short_code


class RecipeIngredient(TimeStampedModel):
    """Связующая модель рецепта и ингредиента."""

    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(INGREDIENT_AMOUNT_MIN),
            MaxValueValidator(INGREDIENT_AMOUNT_MAX),
        ],
    )

    class Meta:
        """Мета-класс модели."""

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        ]
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self) -> str:
        """Вернуть строковое представление ингредиента рецепта."""
        return f'{self.ingredient} - {self.amount}'


class Favorite(TimeStampedModel):
    """Модель избранного рецепта."""

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='favorites',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        to=Recipe,
        related_name='favorited_by',
        on_delete=models.CASCADE,
    )

    class Meta:
        """Мета-класс модели."""

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_user_favorites',
            ),
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self) -> str:
        """Вернуть строковое представление избранного."""
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(TimeStampedModel):
    """Модель списка покупок."""

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        to=Recipe,
        related_name='in_carts',
        on_delete=models.CASCADE,
    )

    class Meta:
        """Мета-класс модели."""

        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_user_cart',
            ),
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self) -> str:
        """Вернуть строковое представление элемента списка покупок."""
        return f'{self.user} -> {self.recipe}'

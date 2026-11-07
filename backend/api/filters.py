from typing import TYPE_CHECKING

import django_filters
from django.db.models import QuerySet

from recipes.models import Ingredient, Recipe


if TYPE_CHECKING:
    from rest_framework.request import Request


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    tags = django_filters.AllValuesMultipleFilter(method='filter_tags')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        """Мета-класс фильтра."""

        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(
        self,
        queryset: QuerySet[Recipe],
        _name: str,
        value: int,
    ) -> QuerySet[Recipe]:
        """Отфильтровать рецепты по избранному текущего пользователя."""
        request: Request | None = self.request
        if request is None or not request.user.is_authenticated or not value:
            return queryset

        return queryset.filter(favorites__user=request.user)

    def filter_is_in_shopping_cart(
        self,
        queryset: QuerySet[Recipe],
        _name: str,
        value: int,
    ) -> QuerySet[Recipe]:
        """Отфильтровать рецепты по списку покупок текущего пользователя."""
        request: Request | None = self.request
        if request is None or not request.user.is_authenticated or not value:
            return queryset

        return queryset.filter(shopping_cart__user=request.user)


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        """Мета-класс фильтра."""

        model = Ingredient
        fields = ('name',)

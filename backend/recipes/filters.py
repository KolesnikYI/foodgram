from typing import TYPE_CHECKING

import django_filters
from django.db.models import QuerySet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart


if TYPE_CHECKING:
    from rest_framework.request import Request


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.CharFilter(method='filter_tags')
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        """Мета-класс фильтра."""

        model = Recipe
        fields = ('author', 'tags')

    def filter_tags(
        self,
        queryset: QuerySet[Recipe],
        _name: str,
        _value: str,
    ) -> QuerySet[Recipe]:
        """Отфильтровать рецепты по слагам тегов из query-параметров."""
        request: Request | None = self.request
        if request is None:
            return queryset

        slugs = request.query_params.getlist('tags')
        if not slugs:
            return queryset

        return queryset.filter(tags__slug__in=slugs).distinct()

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

        recipe_ids = Favorite.objects.filter(
            user=request.user,
        ).values_list('recipe_id', flat=True)
        return queryset.filter(id__in=recipe_ids)

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

        recipe_ids = ShoppingCart.objects.filter(
            user=request.user,
        ).values_list('recipe_id', flat=True)
        return queryset.filter(id__in=recipe_ids)


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

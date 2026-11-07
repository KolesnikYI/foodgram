from backend.api.filters import IngredientFilter, RecipeFilter
from backend.api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from django.db.models import Prefetch, QuerySet, Sum
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет только для чтения тегов."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет только для чтения ингредиентов."""

    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вьюсет для списка/получения/создания/изменения/удаления рецептов."""

    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self) -> QuerySet[Recipe]:
        """Вернуть queryset, оптимизированный для list/retrieve."""
        recipe_ingredients = RecipeIngredient.objects.select_related(
            'ingredient',
        )
        return Recipe.objects.select_related('author').prefetch_related(
            'tags',
            Prefetch('recipe_ingredients', queryset=recipe_ingredients),
        )

    def get_serializer_class(self) -> type[RecipeListSerializer]:
        """Вернуть сериализатор в зависимости от текущего действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeListSerializer

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Добавить рецепт в избранное."""
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Удалить рецепт из избранного."""
        recipe = self.get_object()
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не был добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Добавить рецепт в список покупок."""
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Удалить рецепт из списка покупок."""
        recipe = self.get_object()
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не был добавлен в список покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request: Request) -> HttpResponse:
        """Скачать агрегированный список покупок в виде текстового файла."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        lines: list[str] = ['Список покупок', '']
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            lines.append(f'{name} ({unit}) — {amount}')

        content = '\n'.join(lines) + '\n'
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Вернуть короткую ссылку на рецепт."""
        recipe = self.get_object()
        relative_url = f'/s/{recipe.short_code}/'
        return Response(
            {'short-link': request.build_absolute_uri(relative_url)},
        )


def short_link_redirect(
    request: HttpRequest,
    short_code: str,
) -> HttpResponseRedirect:
    """Перенаправить короткую ссылку на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return HttpResponseRedirect(
        request.build_absolute_uri(f'/recipes/{recipe.id}/'),
    )

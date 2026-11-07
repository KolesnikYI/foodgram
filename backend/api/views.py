from io import BytesIO

from django.db.models import Prefetch, QuerySet, Sum
from django.http import (
    FileResponse,
    HttpRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeListSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


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
    """Вьюсет для работы с рецептами."""

    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    def get_queryset(self) -> QuerySet[Recipe]:
        """Вернуть оптимизированный queryset рецептов."""
        recipe_ingredients = RecipeIngredient.objects.select_related(
            'ingredient',
        )
        return Recipe.objects.select_related('author').prefetch_related(
            'tags',
            Prefetch(
                'recipe_ingredients',
                queryset=recipe_ingredients,
            ),
        )

    def get_serializer_class(
        self,
    ) -> type[RecipeListSerializer] | type[RecipeWriteSerializer]:
        """Выбрать сериализатор в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeListSerializer

    def _add_relation(
        self,
        request: Request,
        serializer_class: (
            type[FavoriteSerializer] | type[ShoppingCartSerializer]
        ),
    ) -> Response:
        """Добавить рецепт в избранное или список покупок."""
        recipe = self.get_object()
        serializer = serializer_class(
            data={
                'user': request.user.pk,
                'recipe': recipe.pk,
            },
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def _delete_relation(
        self,
        request: Request,
        model: type[Favorite] | type[ShoppingCart],
        error_message: str,
    ) -> Response:
        """Удалить рецепт из избранного или списка покупок."""
        recipe = self.get_object()
        deleted_count, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

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
        return self._add_relation(request, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Удалить рецепт из избранного."""
        return self._delete_relation(
            request,
            Favorite,
            'Рецепт не был добавлен в избранное.',
        )

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
        return self._add_relation(request, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Удалить рецепт из списка покупок."""
        return self._delete_relation(
            request,
            ShoppingCart,
            'Рецепт не был добавлен в список покупок.',
        )

    @staticmethod
    def _build_shopping_list_file(
        ingredients: QuerySet,
    ) -> FileResponse:
        """Сформировать текстовый файл со списком покупок."""
        lines = ['Список покупок', '']

        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            lines.append(f'{name} ({unit}) — {amount}')

        content = '\n'.join(lines) + '\n'
        buffer = BytesIO(content.encode('utf-8'))
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8',
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(
        self,
        request: Request,
    ) -> FileResponse:
        """Скачать агрегированный список покупок."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user,
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        return self._build_shopping_list_file(ingredients)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
    )
    def get_link(
        self,
        request: Request,
        pk: str | None = None,  # noqa: ARG002
    ) -> Response:
        """Вернуть короткую ссылку на рецепт."""
        recipe = self.get_object()
        relative_url = reverse(
            'short-link-redirect',
            kwargs={'short_code': recipe.short_code},
        )
        return Response(
            {
                'short-link': request.build_absolute_uri(relative_url),
            },
        )


def short_link_redirect(
    request: HttpRequest,
    short_code: str,
) -> HttpResponseRedirect:
    """Перенаправить короткую ссылку на страницу рецепта."""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return HttpResponseRedirect(
        request.build_absolute_uri(f'/recipes/{recipe.pk}/'),
    )

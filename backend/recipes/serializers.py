from typing import cast

from django.db import transaction
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from recipes.serializers_short import RecipeShortSerializer
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from api.fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в составе рецепта (для чтения)."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        """Мета-класс сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта только для чтения."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj: Recipe) -> bool:
        """Вернуть True, если рецепт в избранном у текущего пользователя."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists(),
        )

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        """Вернуть True, если рецепт в списке покупок текущего пользователя."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj,
            ).exists(),
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента при создании/изменении рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        """Мета-класс сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и изменения рецепта."""

    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True, required=True)

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_tags(self, tags: list[Tag]) -> list[Tag]:
        """Проверить, что теги не пусты и не повторяются."""
        if not tags:
            raise serializers.ValidationError(
                'Список тегов не должен быть пустым.',
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.',
            )
        return tags

    def validate_ingredients(
        self,
        ingredients: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Проверить, что ингредиенты не пусты и не повторяются."""
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не должен быть пустым.',
            )
        ingredient_ids = [
            cast('Ingredient', item['ingredient']).id for item in ingredients
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.',
            )
        return ingredients

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Проверить обязательность тегов и ингредиентов при обновлении."""
        if self.instance is not None:
            if 'tags' not in attrs:
                raise serializers.ValidationError(
                    {'tags': 'Поле tags обязательно при обновлении.'},
                )
            if 'ingredients' not in attrs:
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            'Поле ingredients обязательно при обновлении.'
                        ),
                    },
                )
        return attrs

    @staticmethod
    def _set_ingredients(
        recipe: Recipe,
        ingredients: list[dict[str, object]],
    ) -> None:
        """Заменить ингредиенты рецепта через связующую таблицу."""
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=cast('Ingredient', item['ingredient']),
                amount=cast('int', item['amount']),
            )
            for item in ingredients
        )

    @transaction.atomic
    def create(self, validated_data: dict[str, object]) -> Recipe:
        """Создать рецепт с тегами и ингредиентами."""
        tags = cast('list[Tag]', validated_data.pop('tags'))
        ingredients = cast(
            'list[dict[str, object]]',
            validated_data.pop('ingredients'),
        )
        request = self.context.get('request')

        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(
        self,
        instance: Recipe,
        validated_data: dict[str, object],
    ) -> Recipe:
        """Обновить рецепт с тегами и ингредиентами."""
        tags = cast('list[Tag]', validated_data.pop('tags', None))
        ingredients = cast(
            'list[dict[str, object]]',
            validated_data.pop('ingredients', None),
        )

        recipe = super().update(instance, validated_data)

        recipe.tags.set(tags)
        self._set_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def to_representation(self, instance: Recipe) -> dict[str, object]:
        """Вернуть представление рецепта для чтения."""
        return RecipeListSerializer(instance, context=self.context).data


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и списка покупок."""

    class Meta:
        """Мета-класс сериализатора."""

        fields = ('user', 'recipe')

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        """Проверить, что связь ещё не существует."""
        model = self.Meta.model  # type: ignore[attr-defined]
        if model.objects.filter(**attrs).exists():
            raise serializers.ValidationError('Рецепт уже добавлен.')
        return attrs

    def to_representation(
        self,
        instance: Favorite | ShoppingCart,
    ) -> dict[str, object]:
        """Вернуть рецепт в коротком представлении."""
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context,
        ).data


class FavoriteSerializer(BaseRecipeRelationSerializer):
    """Сериализатор добавления рецепта в избранное."""

    class Meta(BaseRecipeRelationSerializer.Meta):
        """Мета-класс сериализатора."""

        model = Favorite


class ShoppingCartSerializer(BaseRecipeRelationSerializer):
    """Сериализатор добавления рецепта в список покупок."""

    class Meta(BaseRecipeRelationSerializer.Meta):
        """Мета-класс сериализатора."""

        model = ShoppingCart

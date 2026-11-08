from typing import Any, cast

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers_short import RecipeShortSerializer
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription


User = get_user_model()


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


class FoodgramUserSerializer(UserSerializer):
    """Cериализатор для модели пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj) -> bool:
        """Вернуть True, если текущий пользователь подписан на obj."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.subscribers.filter(user=request.user).exists()
        )


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта только для чтения."""

    tags = TagSerializer(many=True, read_only=True)
    author = FoodgramUserSerializer(read_only=True)
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
            and obj.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        """Вернуть True, если рецепт в списке покупок текущего пользователя."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.shopping_carts.filter(user=request.user).exists()
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

    def validate_image(self, image: ImageFile) -> ImageFile:
        """Проверить, что переданное изображение не пустое."""
        if not image:
            raise serializers.ValidationError(
                'Изображение не должно быть пустым.',
            )
        return image

    def validate(  # noqa: C901
        self,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """Проверить теги и ингредиенты рецепта."""
        tags = attrs.get('tags')
        ingredients = attrs.get('ingredients')

        if tags is not None:
            if not tags:
                raise serializers.ValidationError(
                    {
                        'tags': 'Список тегов не должен быть пустым.',
                    }
                )

            if len(tags) != len(set(tags)):
                raise serializers.ValidationError(
                    {
                        'tags': 'Теги не должны повторяться.',
                    }
                )

        if ingredients is not None:
            if not ingredients:
                raise serializers.ValidationError(
                    {
                        'ingredients': (
                            'Список ингредиентов не должен быть пустым.'
                        ),
                    }
                )

            ingredient_ids = [
                cast('Ingredient', item['ingredient']).id
                for item in ingredients
            ]

            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    {
                        'ingredients': 'Ингредиенты не должны повторяться.',
                    }
                )

        return attrs

    @staticmethod
    def _set_ingredients(
        recipe: Recipe,
        ingredients: list[dict[str, object]],
    ) -> None:
        """Заменить ингредиенты рецепта через связующую таблицу."""
        recipe.recipe_ingredients.all().delete()
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
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(cast('list[Tag]', tags))

        if ingredients is not None:
            self._set_ingredients(
                recipe=instance,
                ingredients=cast('list[dict[str, object]]', ingredients),
            )

        return super().update(instance, validated_data)


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


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор для установки аватара пользователя."""

    avatar = Base64ImageField()

    def update(
        self,
        instance,
        validated_data: dict[str, object],
    ):
        """Установить аватар пользователя."""
        instance.avatar = validated_data['avatar']
        instance.save(update_fields=['avatar'])
        return instance

    def to_representation(self, instance) -> dict[str, object]:
        """Вернуть представление аватара."""
        return {
            'avatar': instance.avatar.url if instance.avatar else None,
        }


class UserWithRecipesSerializer(FoodgramUserSerializer):
    """Сериализатор пользователя с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True,
    )

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = (
            *FoodgramUserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj) -> list[dict[str, object]]:
        """Вернуть рецепты автора с учётом параметра recipes_limit."""
        request = self.context.get('request')
        queryset = obj.recipes.all()
        raw_limit = request.query_params.get('recipes_limit')
        if raw_limit is not None:
            try:
                limit = int(raw_limit)
            except ValueError:
                limit = 0

            if limit > 0:
                queryset = queryset[:limit]

        return RecipeShortSerializer(
            queryset,
            many=True,
            context={'request': request},
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        """Проверить корректность подписки перед созданием."""
        user = attrs['user']
        author = attrs['author']

        if user == author:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'},
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Подписка уже существует.'},
            )

        return attrs

    def to_representation(self, instance: Subscription) -> dict[str, object]:
        """Вернуть представление автора подписки."""
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context,
        ).data

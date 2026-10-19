from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.serializers_short import RecipeShortSerializer
from rest_framework import serializers
from users.models import Subscription

from api.fields import Base64ImageField


if TYPE_CHECKING:
    from users.models import CustomUser as User
else:
    User = get_user_model()


class CustomUserSerializer(UserSerializer):
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

    def get_is_subscribed(self, obj: User) -> bool:
        """Вернуть True, если текущий пользователь подписан на obj."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user,
                author=obj,
            ).exists(),
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор регистрации с обязательными именем и фамилией."""

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    class Meta(UserCreateSerializer.Meta):
        """Мета-класс сериализатора."""

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор для установки аватара пользователя."""

    avatar = Base64ImageField()

    def update(
        self,
        instance: User,
        validated_data: dict[str, object],
    ) -> User:
        """Установить аватар пользователя."""
        instance.avatar = validated_data['avatar']
        instance.save(update_fields=['avatar'])
        return instance

    def to_representation(self, instance: User) -> dict[str, object]:
        """Вернуть представление аватара."""
        return {
            'avatar': instance.avatar.url if instance.avatar else None,
        }


class UserWithRecipesSerializer(CustomUserSerializer):
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
            *CustomUserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj: User) -> list[dict[str, object]]:
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

    def validate(self, attrs: dict[str, User]) -> dict[str, User]:
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

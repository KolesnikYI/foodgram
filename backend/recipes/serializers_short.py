from recipes.models import Recipe
from rest_framework import serializers


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта, используемое в подписках и корзине."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

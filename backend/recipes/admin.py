from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели тега."""

    list_display = ('id', 'name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('created_at',)
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # noqa: RUF012


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели ингредиента."""

    list_display = ('id', 'name', 'measurement_unit', 'created_at')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', 'created_at')
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для RecipeIngredient в админке рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели рецепта."""

    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorites_count',
        'created_at',
    )
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags', 'created_at')
    ordering = ('-created_at',)
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)
    list_select_related = ('author',)

    @admin.display(description='В избранном')
    def favorites_count(self, obj: Recipe) -> int:
        """Вернуть количество добавлений рецепта в избранное."""
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели ингредиента рецепта."""

    list_display = ('id', 'recipe', 'ingredient', 'amount', 'created_at')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели избранного."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели списка покупок."""

    list_display = ('id', 'user', 'recipe', 'created_at')
    search_fields = ('user__email', 'user__username', 'recipe__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('user', 'recipe')

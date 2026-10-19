from django.urls import include, path
from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet


class NoSuffixRouter(DefaultRouter):
    """Класс с отключенным форматированием суффиксов в эндпоинтах.

    В связке с React нет необходимости в '.json' / '.xml' суффиксах. А если
    оставить этот флаг из наследуемого класса - будет конфликт повторной
    регистрации 'users' с djoser.
    """

    include_format_suffixes = False


router = NoSuffixRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls')),
    path('', include(router.urls)),
]

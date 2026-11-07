from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class UserAdminConfig(UserAdmin):
    """Админ-конфигурация модели пользователя."""

    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (
            'Персональная информация',
            {'fields': ('first_name', 'last_name', 'avatar')},
        ),
        (
            'Права доступа',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'username',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                ),
            },
        ),
    )

    readonly_fields = ('date_joined', 'last_login')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-конфигурация модели подписки."""

    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__email', 'author__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('user', 'author')

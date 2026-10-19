from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request


class IsAuthorOrReadOnly(BasePermission):
    """Чтение доступно всем, изменение - только автору объекта."""

    def has_object_permission(
        self,
        request: Request,
        _view: object,
        obj: object,
    ) -> bool:
        """Проверить права на уровне объекта."""
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and obj.author_id == request.user.id
        )

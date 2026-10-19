from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request


class SafeTokenAuthentication(TokenAuthentication):
    """Считать недействительный токен анонимным на безопасных методах."""

    def authenticate(
        self,
        request: Request,
    ) -> tuple[object, object] | None:
        """Аутентифицировать по токену, игнорируя неверный на GET/HEAD."""
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            if request.method in SAFE_METHODS:
                return None
            raise

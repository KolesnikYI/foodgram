from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from users.models import Subscription
from users.serializers import (
    SetAvatarSerializer,
    SubscriptionCreateSerializer,
    UserWithRecipesSerializer,
)

from api.pagination import LimitPageNumberPagination


User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """ViewSet пользователя с подписками и аватаром."""

    pagination_class = LimitPageNumberPagination

    def get_permissions(self) -> list[BasePermission]:
        """Требовать авторизацию для /users/me/."""
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request: Request) -> Response:
        """Установить аватар текущего пользователя."""
        serializer = SetAvatarSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        """Удалить аватар текущего пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request: Request, **kwargs: str) -> Response:
        """Подписать текущего пользователя на автора."""
        author = get_object_or_404(User, pk=kwargs.get('id'))
        serializer = SubscriptionCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request: Request, **kwargs: str) -> Response:
        """Отписать текущего пользователя от автора."""
        author = get_object_or_404(User, pk=kwargs.get('id'))
        deleted_count, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request: Request) -> Response:
        """Вернуть авторов, на которых подписан текущий пользователь."""
        authors = (
            User.objects.filter(subscribers__user=request.user)
            .distinct()
            .order_by('id')
        )
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

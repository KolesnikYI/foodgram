from rest_framework.pagination import PageNumberPagination

from config.constants import PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинатор с параметрами page/limit."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'

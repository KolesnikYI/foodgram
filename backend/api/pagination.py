from config.constants import PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинатор с параметрами page/limit."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'

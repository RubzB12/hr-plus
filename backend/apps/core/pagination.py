from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination configuration for list endpoints.

    - Default page size: 50 items
    - Client can request different page size via 'page_size' query param
    - Maximum page size: 100 items (prevents excessive memory usage)
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

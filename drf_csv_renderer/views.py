from typing import Any, List, Dict

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework import generics
from rest_framework.request import Request

from drf_csv_renderer.mixins import CSVResponseMixin


class CSVListView(CSVResponseMixin, generics.ListAPIView):
    """List view with CSV export functionality."""

    def list(
        self, request: Request, *args, **kwargs
    ) -> HttpResponse | StreamingHttpResponse:
        """Override to return CSV response."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Get data for CSV export."""
        queryset = self.filter_queryset(self.get_queryset())

        # Apply row count limit at the queryset level for better performance
        row_count = self.get_csv_row_count()
        if row_count is not None and hasattr(queryset, "__getitem__"):
            queryset = queryset[:row_count]

        if self.csv_streaming:
            if hasattr(self, "serializer_class") and self.serializer_class:
                return self._get_serialized_stream(queryset, row_count)
            else:
                return (item for item in queryset.values())

        page = self.paginate_queryset(queryset)
        if page is not None:
            queryset = page

        if hasattr(self, "serializer_class") and self.serializer_class:
            serializer = self.get_serializer(queryset, many=True)
            return serializer.data

        return list(queryset.values())

    def _get_serialized_stream(self, queryset, row_count: int = None):
        """Generator that yields serialized objects one by one."""
        serializer_class = self.get_serializer_class()
        count = 0
        chunk_size = getattr(self, "csv_chunk_size", 1000)

        # Check if queryset has prefetch_related applied
        if (
            hasattr(queryset, "_prefetch_related_lookups")
            and queryset._prefetch_related_lookups
        ):
            # Use iterator with chunk_size for prefetch_related querysets
            iterator = queryset.iterator(chunk_size=chunk_size)
        else:
            # Use regular iterator for simple querysets
            iterator = queryset.iterator()

        for obj in iterator:
            if row_count is not None and count >= row_count:
                break

            serializer = serializer_class(obj, context=self.get_serializer_context())
            yield serializer.data
            count += 1


class CSVGenericView(CSVResponseMixin, generics.GenericAPIView):
    """Generic view for custom CSV responses."""

    def get(
        self, request: Request, *args, **kwargs
    ) -> HttpResponse | StreamingHttpResponse:
        """Handle GET requests."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Override this method to provide custom data."""
        raise NotImplementedError("Subclasses must implement get_csv_data() method")

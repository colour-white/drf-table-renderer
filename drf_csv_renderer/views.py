from typing import Any, List, Dict

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework import generics
from rest_framework.request import Request

from drf_csv_renderer.mixins import CSVResponseMixin


class CSVListView(CSVResponseMixin, generics.ListAPIView):
    """List view with CSV export functionality."""

    def list(self, request: Request, *args, **kwargs) -> HttpResponse | StreamingHttpResponse:
        """Override to return CSV response."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Get data for CSV export."""
        queryset = self.filter_queryset(self.get_queryset())
        rows_count = self.get_csv_rows_count()

        if self.csv_streaming:
            # Apply limit to queryset for streaming
            if rows_count is not None:
                queryset = queryset[:rows_count]

            if hasattr(self, "serializer_class") and self.serializer_class:
                return self._get_serialized_stream(queryset)
            else:
                return (item for item in queryset.values())

        # For non-streaming, apply limit to queryset
        if rows_count is not None:
            queryset = queryset[:rows_count]

        page = self.paginate_queryset(queryset)
        if page is not None:
            queryset = page

        if hasattr(self, "serializer_class") and self.serializer_class:
            serializer = self.get_serializer(queryset, many=True)
            return serializer.data

        return list(queryset.values())

    def _get_serialized_stream(self, queryset):
        """Generator that yields serialized objects one by one."""
        serializer_class = self.get_serializer_class()

        try:
            # Try to use iterator() without chunk_size first
            iterator = queryset.iterator()
        except ValueError as e:
            if "chunk_size must be provided" in str(e):
                # Fall back to using chunk_size when prefetch_related is used
                chunk_size = getattr(self, 'csv_streaming_chunk_size', 1000)
                iterator = queryset.iterator(chunk_size=chunk_size)
            else:
                raise

        for obj in iterator:
            serializer = serializer_class(obj, context=self.get_serializer_context())
            yield serializer.data


class CSVGenericView(CSVResponseMixin, generics.GenericAPIView):
    """Generic view for custom CSV responses."""

    def get(self, request: Request, *args, **kwargs) -> HttpResponse | StreamingHttpResponse:
        """Handle GET requests."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Override this method to provide custom data."""
        raise NotImplementedError("Subclasses must implement get_csv_data() method")

    def apply_rows_limit(self, data: Any) -> Any:
        """Apply rows limit to data if specified."""
        rows_count = self.get_csv_rows_count()
        if rows_count is not None:
            if isinstance(data, list):
                return data[:rows_count]
            elif hasattr(data, "__iter__") and not isinstance(data, (str, bytes, dict)):
                return (item for i, item in enumerate(data) if i < rows_count)
        return data
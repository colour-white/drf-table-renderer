from typing import Any, List, Dict

from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from drf_csv_renderer.mixins import CSVResponseMixin


class CSVListView(CSVResponseMixin, generics.ListAPIView):
    """List view with CSV export functionality."""

    def list(self, request: Request, *args, **kwargs) -> Response | StreamingHttpResponse:
        """Override to return CSV response."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Get data for CSV export."""
        queryset = self.filter_queryset(self.get_queryset())

        if self.csv_streaming:
            if hasattr(self, "serializer_class") and self.serializer_class:
                return self._get_serialized_stream(queryset)
            else:
                return (item for item in queryset.values())

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
        for obj in queryset.iterator():  # Use iterator() for memory efficiency
            serializer = serializer_class(obj, context=self.get_serializer_context())
            yield serializer.data


class CSVGenericView(CSVResponseMixin, generics.GenericAPIView):
    """Generic view for custom CSV responses."""

    def get(self, request: Request, *args, **kwargs) -> Response | StreamingHttpResponse:
        """Handle GET requests."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Override this method to provide custom data."""
        raise NotImplementedError("Subclasses must implement get_csv_data() method")

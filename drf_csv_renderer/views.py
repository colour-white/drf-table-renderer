from typing import Any, List, Dict

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework import generics
from rest_framework.request import Request

from drf_csv_renderer.mixins import CSVResponseMixin


class CSVListView(CSVResponseMixin, generics.ListAPIView):
    """List view with CSV export functionality."""

    # Configuration for streaming iterator
    csv_iterator_chunk_size: int = 1000

    def list(self, request: Request, *args, **kwargs) -> HttpResponse | StreamingHttpResponse:
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
                return self._get_values_stream(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            queryset = page

        if hasattr(self, "serializer_class") and self.serializer_class:
            serializer = self.get_serializer(queryset, many=True)
            return serializer.data

        return list(queryset.values())

    def _get_serialized_stream(self, queryset):
        """Generator that yields serialized data dictionaries one by one."""
        serializer_class = self.get_serializer_class()

        # Check if queryset has prefetch_related applied
        if queryset._prefetch_related_lookups:
            # Use chunk_size when prefetch_related is used
            iterator = queryset.iterator(chunk_size=self.csv_iterator_chunk_size)
        else:
            # Use iterator without chunk_size for simple queries
            iterator = queryset.iterator()

        for obj in iterator:
            serializer = serializer_class(obj, context=self.get_serializer_context())
            # Ensure we're yielding actual data, not the serializer
            yield serializer.data

    def _get_values_stream(self, queryset):
        """Generator that yields queryset values one by one."""
        # For values(), we need to handle prefetch_related differently
        if queryset._prefetch_related_lookups:
            # Clear prefetch_related for values() as it's not compatible
            queryset = queryset.prefetch_related(None)

        # Use iterator for values
        try:
            for obj in queryset.iterator(chunk_size=self.csv_iterator_chunk_size):
                # Convert model instance to dict
                yield {field.name: getattr(obj, field.name) for field in obj._meta.fields}
        except ValueError:
            # Fallback to regular iteration if iterator still fails
            for obj in queryset:
                yield {field.name: getattr(obj, field.name) for field in obj._meta.fields}


class CSVGenericView(CSVResponseMixin, generics.GenericAPIView):
    """Generic view for custom CSV responses."""

    def get(self, request: Request, *args, **kwargs) -> HttpResponse | StreamingHttpResponse:
        """Handle GET requests."""
        data = self.get_csv_data()
        return self.create_csv_response(data)

    def get_csv_data(self) -> List[Dict[str, Any]] | Any:
        """Override this method to provide custom data."""
        raise NotImplementedError("Subclasses must implement get_csv_data() method")
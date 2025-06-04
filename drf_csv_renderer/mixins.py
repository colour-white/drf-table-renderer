from typing import Type, Optional, Dict, Any
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from drf_csv_renderer.renderers import (
    CSVRenderer,
    StreamingCSVRenderer,
    BaseCSVRenderer,
)


class CSVConfigurationMixin:
    """Mixin for CSV configuration options."""

    csv_filename: Optional[str] = None
    csv_streaming: bool = False
    csv_renderer_class: Type[CSVRenderer] = CSVRenderer
    csv_streaming_renderer_class: Type[StreamingCSVRenderer] = StreamingCSVRenderer
    csv_flatten_nested: bool = True
    csv_preserve_lists: bool = True
    csv_nested_separator: str = "__"
    csv_writer_options: Dict = None
    csv_row_count: Optional[int] = None
    csv_chunk_size: int = 1000

    def get_csv_filename(self) -> str:
        """Get filename for CSV download."""
        if self.csv_filename:
            return self.csv_filename
        return f"{self.__class__.__name__.lower().replace('view', '')}.csv"

    def get_csv_row_count(self) -> Optional[int]:
        """Get row count limit from request parameters or class attribute."""

        if hasattr(self, "request") and self.request:
            try:
                param_count = self.request.query_params.get("csv_row_count")
                if param_count is not None:
                    return int(param_count)
            except (ValueError, TypeError):
                pass

        # Fall back to class attribute
        return self.csv_row_count

    def get_csv_renderer(self) -> BaseCSVRenderer:
        """Get configured CSV renderer instance."""
        renderer_class = (
            self.csv_streaming_renderer_class
            if self.csv_streaming
            else self.csv_renderer_class
        )
        renderer = renderer_class()

        # Configure flattening
        renderer.configure_flattening(
            separator=self.csv_nested_separator,
            enabled=self.csv_flatten_nested,
            preserve_lists=self.csv_preserve_lists,
        )

        # Configure writer options
        if self.csv_writer_options:
            renderer.writer_opts.update(self.csv_writer_options)

        return renderer


class CSVResponseMixin(CSVConfigurationMixin):
    """Mixin that provides CSV response functionality."""

    def create_csv_response(
        self, data: Any, status_code: int = status.HTTP_200_OK
    ) -> HttpResponse | StreamingHttpResponse:
        """Create appropriate CSV response based on configuration."""
        # Apply row count limit if specified
        row_count = self.get_csv_row_count()
        if row_count is not None:
            data = self._limit_data(data, row_count)

        renderer = self.get_csv_renderer()
        filename = self.get_csv_filename()

        if self.csv_streaming:
            return self._create_streaming_response(data, renderer, filename)
        else:
            return self._create_standard_response(data, renderer, filename, status_code)

    def _limit_data(self, data: Any, row_count: int) -> Any:
        """Limit data to specified row count."""
        if row_count <= 0:
            return []

        if hasattr(data, "__iter__") and not isinstance(data, (str, bytes, dict)):
            # Handle iterables (including generators)
            if hasattr(data, "__getitem__"):
                # List-like objects
                return data[:row_count]
            else:
                # Generators or other iterators
                return self._limit_iterator(data, row_count)
        elif isinstance(data, list):
            return data[:row_count]
        else:
            # Single item - return as is if row_count > 0
            return data

    def _limit_iterator(self, iterator, row_count: int):
        """Create a limited iterator from another iterator."""
        count = 0
        for item in iterator:
            if count >= row_count:
                break
            yield item
            count += 1

    def _create_standard_response(
        self, data: Any, renderer: CSVRenderer, filename: str, status_code: int
    ) -> Response:
        """Create standard CSV response."""
        rendered_content = renderer.render(data)
        response = Response(
            rendered_content, status=status_code, content_type=renderer.media_type
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _create_streaming_response(
        self, data: Any, renderer: StreamingCSVRenderer, filename: str
    ) -> StreamingHttpResponse:
        """Create streaming CSV response."""
        csv_stream = renderer.render(data)
        response = StreamingHttpResponse(csv_stream, content_type=renderer.media_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

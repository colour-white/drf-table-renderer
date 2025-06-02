from typing import Type, Optional, Dict, Any
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from drf_csv_renderer.renderers import CSVRenderer, StreamingCSVRenderer, BaseCSVRenderer


class CSVConfigurationMixin:
    """Mixin for CSV configuration options."""

    csv_filename: Optional[str] = None
    csv_streaming: bool = False
    csv_renderer_class: Type[CSVRenderer] = CSVRenderer
    csv_streaming_renderer_class: Type[StreamingCSVRenderer] = StreamingCSVRenderer
    csv_flatten_nested: bool = True
    csv_preserve_lists: bool = True  # NEW: Option to preserve lists
    csv_nested_separator: str = "__"
    csv_writer_options: Dict = None

    def get_csv_filename(self) -> str:
        """Get filename for CSV download."""
        if self.csv_filename:
            return self.csv_filename
        return f"{self.__class__.__name__.lower().replace('view', '')}.csv"

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
        renderer = self.get_csv_renderer()
        filename = self.get_csv_filename()

        if self.csv_streaming:
            return self._create_streaming_response(data, renderer, filename)
        else:
            return self._create_standard_response(data, renderer, filename, status_code)

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

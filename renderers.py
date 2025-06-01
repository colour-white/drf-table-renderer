import csv
import io
import json
from typing import List, Dict, Any, Iterator, Optional, Union
from rest_framework import renderers

from utilities import DataFlattener, FieldnameManager


class BaseCSVRenderer(renderers.BaseRenderer):
    """Base CSV renderer with common functionality."""

    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def __init__(self):
        self.writer_opts = {}
        self.flattener = DataFlattener()
        self.fieldname_manager = FieldnameManager()

    def configure_flattening(
        self, separator: str = "__", enabled: bool = True, preserve_lists: bool = True
    ):
        """Configure data flattening options."""
        self.flattener = DataFlattener(
            separator=separator, flatten_enabled=enabled, preserve_lists=preserve_lists
        )

    def _prepare_data(self, data: Any) -> List[Dict[str, Any]]:
        """Prepare and validate input data."""
        if data is None:
            return []

        if not isinstance(data, list):
            data = [data]

        return data

    def _flatten_all_data(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Flatten all items in the data list."""
        return [self.flattener.flatten_data(item) for item in data]

    def _serialize_value(self, value: Any) -> str:
        """Serialize complex values for CSV output."""
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        elif value is None:
            return ""
        else:
            return str(value)


class CSVRenderer(BaseCSVRenderer):
    """Standard CSV renderer for complete data sets."""

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[Dict] = None,
    ) -> bytes:
        """Render data to CSV format."""
        prepared_data = self._prepare_data(data)
        if not prepared_data:
            return b""

        # Flatten all data
        flattened_data = self._flatten_all_data(prepared_data)

        # Get fieldnames and ensure consistency
        fieldnames = self.fieldname_manager.collect_fieldnames(flattened_data)
        consistent_data = self.fieldname_manager.ensure_consistent_data(
            flattened_data, fieldnames
        )

        return self._write_csv(consistent_data, fieldnames)

    def _write_csv(self, data: List[Dict[str, Any]], fieldnames: List[str]) -> bytes:
        """Write data to CSV format."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, **self.writer_opts)

        writer.writeheader()

        # Serialize complex values before writing
        for row in data:
            serialized_row = {
                field: self._serialize_value(value) for field, value in row.items()
            }
            writer.writerow(serialized_row)

        return output.getvalue().encode(self.charset)


class StreamingCSVRenderer(BaseCSVRenderer):
    """True streaming CSV renderer for large datasets."""

    def __init__(self):
        super().__init__()
        self.sample_size = 100

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[Dict] = None,
    ) -> Iterator[bytes]:
        """Return iterator for streaming CSV data."""
        if hasattr(data, "__iter__") and not isinstance(data, (str, bytes, dict)):
            return self._generate_streaming_csv(data)
        else:
            prepared_data = self._prepare_data(data)
            if not prepared_data:
                return iter([b""])
            return self._generate_streaming_csv(prepared_data)

    def _generate_streaming_csv(self, data_iterable) -> Iterator[bytes]:
        """Generate CSV data stream without loading all data into memory."""
        data_iter = iter(data_iterable)

        first_batch = []
        try:
            for _ in range(self.sample_size):
                first_batch.append(next(data_iter))
        except StopIteration:
            pass

        if not first_batch:
            yield b""
            return

        fieldnames = self._determine_fieldnames_from_batch(first_batch)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, **self.writer_opts)

        writer.writeheader()
        yield output.getvalue().encode(self.charset)
        self._reset_buffer(output)

        for item in first_batch:
            yield from self._process_and_yield_item(item, fieldnames, writer, output)

        for item in data_iter:
            yield from self._process_and_yield_item(item, fieldnames, writer, output)

    def _determine_fieldnames_from_batch(self, batch: List[Any]) -> List[str]:
        """Determine fieldnames from a batch of data."""
        flattened_batch = self._flatten_all_data(batch)
        return self.fieldname_manager.collect_fieldnames(flattened_batch)

    def _process_and_yield_item(
        self,
        item: Any,
        fieldnames: List[str],
        writer: csv.DictWriter,
        output: io.StringIO,
    ) -> Iterator[bytes]:
        """Process a single item and yield its CSV representation."""
        flattened_item = self.flattener.flatten_data(item)
        row = {field: flattened_item.get(field, "") for field in fieldnames}

        serialized_row = {
            field: self._serialize_value(value) for field, value in row.items()
        }

        writer.writerow(serialized_row)
        yield output.getvalue().encode(self.charset)
        self._reset_buffer(output)

    def _reset_buffer(self, buffer: io.StringIO):
        """Reset string buffer for reuse."""
        buffer.truncate(0)
        buffer.seek(0)

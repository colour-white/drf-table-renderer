# DRF Excel Renderer

A flexible Django REST Framework renderer for exporting data as CSV with advanced features including nested data flattening, streaming support, and configurable field handling.

## Features

- **Standard & Streaming CSV Export** - Handle both small and large datasets efficiently
- **Nested Data Flattening** - Automatically flatten nested dictionaries and objects
- **Configurable Field Handling** - Preserve lists, customize separators, and control flattening behavior
- **Easy Integration** - Simple mixins for existing DRF views
- **Memory Efficient** - Streaming support for large datasets without memory issues

## Installation

```bash
uv add drf-excel-renderer
```

## Quick Start

### Basic Usage

```python
from drf_excel_plus.views import CSVListView
from myapp.models import MyModel
from myapp.serializers import MyModelSerializer

class MyModelCSVView(CSVListView):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    csv_filename = 'my_data.csv'
```

### With Custom Configuration

```python
class CustomCSVView(CSVListView):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    
    # CSV Configuration
    csv_filename = 'custom_export.csv'
    csv_streaming = True  # Enable streaming for large datasets
    csv_flatten_nested = True  # Flatten nested objects
    csv_preserve_lists = False  # Convert lists to comma-separated strings
    csv_nested_separator = '.'  # Use dots instead of underscores
    csv_writer_options = {'delimiter': ';'}  # Custom CSV writer options
```

### Generic View for Custom Data

```python
from drf_excel_plus.views import CSVGenericView

class CustomDataCSVView(CSVGenericView):
    csv_filename = 'custom_data.csv'
    
    def get_csv_data(self):
        # Return any data structure
        return [
            {'name': 'John', 'details': {'age': 30, 'city': 'NYC'}},
            {'name': 'Jane', 'details': {'age': 25, 'city': 'LA'}}
        ]
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `csv_filename` | `None` | Custom filename for CSV download |
| `csv_streaming` | `False` | Enable streaming for large datasets |
| `csv_flatten_nested` | `True` | Flatten nested dictionaries |
| `csv_preserve_lists` | `True` | Keep lists as JSON vs comma-separated |
| `csv_nested_separator` | `"__"` | Separator for nested field names |
| `csv_writer_options` | `{}` | Additional options for CSV writer |

## Data Flattening Examples

### Nested Objects
```python
# Input
{'user': {'name': 'John', 'profile': {'age': 30}}}

# Output (flattened)
{'user__name': 'John', 'user__profile__age': 30}
```

### Lists Handling
```python
# With preserve_lists=True (default)
{'tags': ['python', 'django']} → {'tags': ['python', 'django']}

# With preserve_lists=False
{'tags': ['python', 'django']} → {'tags': 'python, django'}
```

## URL Configuration

```python
from django.urls import path
from myapp.views import MyModelCSVView

urlpatterns = [
    path('api/export/csv/', MyModelCSVView.as_view(), name='csv-export'),
]
```

## Advanced Usage

### Using Mixins Directly

```python
from rest_framework import generics
from drf_excel_plus.mixins import CSVResponseMixin

class MyCustomView(CSVResponseMixin, generics.ListAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    csv_streaming = True
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('format') == 'csv':
            data = self.get_csv_data()
            return self.create_csv_response(data)
        return super().get(request, *args, **kwargs)
```

### Custom Renderer

```python
from drf_excel_plus.renderers import CSVRenderer

class CustomCSVRenderer(CSVRenderer):
    def _serialize_value(self, value):
        # Custom serialization logic
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        return super()._serialize_value(value)
```

## Performance Considerations

- Use `csv_streaming = True` for datasets larger than 1000 records
- Streaming mode uses minimal memory but may be slower for small datasets
- Consider pagination for very large exports
- Nested flattening adds processing overhead

## Requirements

- Python >= 3.12
- Django >= 3.2
- Django REST Framework >= 3.12

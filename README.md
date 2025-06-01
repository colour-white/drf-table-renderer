# Django REST Framework CSV Renderer

A powerful and flexible CSV renderer library for Django REST Framework that provides both standard and streaming CSV export capabilities with advanced data flattening and configuration options.

## Features

- **Standard & Streaming CSV Export**: Choose between complete data loading or memory-efficient streaming
- **Smart Data Flattening**: Automatically flatten nested objects and relationships
- **List Preservation**: Keep lists as JSON arrays or convert to comma-separated strings
- **True Streaming**: Process large datasets without loading everything into memory
- **Flexible Configuration**: Extensive customization options for CSV output
- **DRF Integration**: Seamlessly integrates with existing DRF views and serializers
- **QuerySet Optimization**: Uses Django's `iterator()` for memory-efficient database queries

## Installation

```bash
pip install drf-csv-renderer
```

## Quick Start

### Basic Usage

```python
# views.py
from drf_csv_renderer.views import CSVListView
from .models import User
from .serializers import UserSerializer

class UserCSVExportView(CSVListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    csv_filename = 'users.csv'
```

### Streaming for Large Datasets

```python
class UserStreamingCSVView(CSVListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    csv_filename = 'users_stream.csv'
    csv_streaming = True  # Enable true streaming
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `csv_filename` | `None` | Custom filename for CSV download |
| `csv_streaming` | `False` | Enable streaming response for large datasets |
| `csv_flatten_nested` | `True` | Flatten nested objects and relationships |
| `csv_preserve_lists` | `True` | Keep lists as JSON arrays vs comma-separated strings |
| `csv_nested_separator` | `'__'` | Separator for flattened nested field names |
| `csv_writer_options` | `{}` | Additional options for Python's csv.DictWriter |

## Advanced Usage

### Custom CSV Configuration

```python
class ConfiguredCSVView(CSVListView):
    queryset = User.objects.select_related('profile')
    serializer_class = UserDetailSerializer
    
    # CSV Configuration
    csv_filename = 'detailed_users.csv'
    csv_streaming = True
    csv_flatten_nested = True
    csv_preserve_lists = False  # Convert lists to "item1, item2"
    csv_nested_separator = '.'  # Use dots instead of underscores
    csv_writer_options = {
        'delimiter': ';',
        'quotechar': '"',
        'quoting': csv.QUOTE_MINIMAL
    }
```

### Custom Data Processing

```python
from drf_csv_renderer.views import CSVGenericView

class CustomReportCSVView(CSVGenericView):
    csv_filename = 'custom_report.csv'
    csv_streaming = True
    
    def get_csv_data(self):
        # Return a generator for memory-efficient streaming
        def data_generator():
            for user in User.objects.iterator():
                yield {
                    'user_id': user.id,
                    'username': user.username,
                    'profile': {
                        'phone': user.profile.phone,
                        'bio': user.profile.bio
                    },
                    'tags': ['admin', 'active'],  # Preserved as JSON array
                    'created_at': user.date_joined
                }
        return data_generator()
```

## Data Flattening Examples

### Nested Objects

**Input:**
```python
{
    'user': {
        'name': 'John Doe',
        'profile': {
            'phone': '+1234567890',
            'address': {
                'city': 'New York',
                'country': 'USA'
            }
        }
    }
}
```

**CSV Output (with `csv_nested_separator='__'`):**
```csv
user__name,user__profile__phone,user__profile__address__city,user__profile__address__country
John Doe,+1234567890,New York,USA
```

### List Handling

**Input:**
```python
{
    'username': 'john_doe',
    'tags': ['admin', 'developer', 'active'],
    'permissions': ['read', 'write', 'delete']
}
```

**With `csv_preserve_lists=True` (default):**
```csv
username,tags,permissions
john_doe,"[""admin"", ""developer"", ""active""]","[""read"", ""write"", ""delete""]"
```

**With `csv_preserve_lists=False`:**
```csv
username,tags,permissions
john_doe,"admin, developer, active","read, write, delete"
```

## Performance Considerations

### Memory Usage

- **Standard Mode**: Loads all data into memory - suitable for smaller datasets
- **Streaming Mode**: Processes one record at a time - ideal for large datasets

### Database Optimization

```python
class OptimizedCSVView(CSVListView):
    # Use select_related for foreign keys to reduce queries
    queryset = User.objects.select_related('profile', 'department')
    
    # Use prefetch_related for many-to-many and reverse foreign keys
    # queryset = User.objects.prefetch_related('groups', 'user_permissions')
    
    csv_streaming = True  # Enable streaming for large datasets
```

## URL Configuration

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Standard CSV export
    path('users/export/', views.UserCSVExportView.as_view(), name='users-csv'),
    
    # Streaming CSV export
    path('users/export/stream/', views.UserStreamingCSVView.as_view(), name='users-csv-stream'),
    
    # Custom CSV report
    path('reports/custom/', views.CustomReportCSVView.as_view(), name='custom-csv'),
]
```

## Integration with DRF Features

### Filtering and Pagination

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class FilteredCSVView(CSVListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    # DRF filtering works automatically
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'date_joined']
    search_fields = ['username', 'email']
    ordering_fields = ['date_joined', 'username']
    
    # Pagination is automatically handled for non-streaming responses
    csv_streaming = False  # Respects pagination
    # csv_streaming = True   # Ignores pagination for full dataset
```

### Permissions and Authentication

```python
from rest_framework.permissions import IsAuthenticated

class SecureCSVView(CSVListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Standard DRF permissions
    csv_filename = 'secure_users.csv'
```

## Response Headers

The library automatically sets appropriate headers for CSV downloads:

```http
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="users.csv"
```

For streaming responses, the `Transfer-Encoding: chunked` header is automatically added.

## Error Handling

```python
class RobustCSVView(CSVListView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_csv_data(self):
        try:
            return super().get_csv_data()
        except Exception as e:
            # Log error and return empty dataset or handle gracefully
            logger.error(f"CSV export error: {e}")
            return []
```

## Best Practices

1. **Use streaming for large datasets** (>10k records)
2. **Optimize database queries** with `select_related()` and `prefetch_related()`
3. **Set appropriate timeouts** for large exports
4. **Consider background tasks** for very large datasets using Celery
5. **Test memory usage** with realistic data volumes
6. **Use meaningful filenames** with timestamps if needed

## Requirements

- Python 3.7+
- Django 3.2+
- Django REST Framework 3.12+

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### v1.0.0
- Initial release
- Standard and streaming CSV export
- Data flattening with configurable options
- List preservation options
- Full DRF integration
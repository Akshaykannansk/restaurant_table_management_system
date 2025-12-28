from rest_framework import viewsets
from core.models import Table
from .serializers import TableSerializer

class TableViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows tables to be viewed.
    Using ReadOnly because logic is complex in Service layer.
    """
    queryset = Table.objects.all().order_by('table_number')
    serializer_class = TableSerializer

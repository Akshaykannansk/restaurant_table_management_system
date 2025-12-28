from rest_framework import serializers
from core.models import Table, Order, TableStatus

class TableSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_order_id = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'table_number', 'seating_capacity', 'status', 'status_display', 'active_order_id']

    def get_active_order_id(self, obj):
        order = obj.active_order
        return order.id if order else None

from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Table, TableStatus, Order, OrderStatus, OrderItem, Bill, BillStatus, MenuItem
from decimal import Decimal
from restaurant_system.celery import app as celery_app

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class TableService:
    @staticmethod
    def get_table(table_id):
        return Table.objects.get(id=table_id)

    @staticmethod
    def is_available(table: Table):
        return table.status == TableStatus.AVAILABLE

    @staticmethod
    def broadcast_update(table_id):
        """
        Sends a WebSocket message to the 'tables' group.
        """
        layer = get_channel_layer()
        # We need to re-fetch to get latest status if not passed
        try:
            table = Table.objects.get(id=table_id)
            async_to_sync(layer.group_send)(
                'tables',
                {
                    'type': 'table_update',
                    'message': {
                        'table_id': table.id,
                        'status': table.status,
                        'table_number': table.table_number
                    }
                }
            )
        except Table.DoesNotExist:
            pass

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(table_id, items_data: list):
        """
        items_data = [{'menu_item_id': 1, 'quantity': 2}, ...]
        """
        table = Table.objects.select_for_update().get(id=table_id)
        
        if table.status != TableStatus.AVAILABLE:
            raise ValidationError(f"Table {table.table_number} is not AVAILABLE (Status: {table.status})")

        # Create Order
        order = Order.objects.create(table=table, status=OrderStatus.PLACED)
        
        # Add Items
        total_items = 0
        for item in items_data:
            menu_item = MenuItem.objects.get(id=item['menu_item_id'])
            if not menu_item.is_available:
                raise ValidationError(f"Item {menu_item.name} is not available")
            
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item['quantity'],
                price_snapshot=menu_item.price
            )
            total_items += 1

        if total_items == 0:
            raise ValidationError("Cannot create empty order")

        # Update Table Status
        table.status = TableStatus.OCCUPIED
        table.save()

        # Trigger Kitchen Notification
        from core.tasks import notify_kitchen
        # Use on_commit to ensure transaction is done before task starts logic (if using DB)
        transaction.on_commit(lambda: notify_kitchen.delay(order.id))
        
        # WebSocket Update
        transaction.on_commit(lambda: TableService.broadcast_update(table_id))
        
        return order

    @staticmethod
    @transaction.atomic
    def update_order_status(order_id, new_status):
        order = Order.objects.select_for_update().get(id=order_id)
        
        # Validate transitions
        if order.status == OrderStatus.SERVED and new_status != OrderStatus.SERVED:
             raise ValidationError("Cannot change status of SERVED order")
        
        # If moving to IN_KITCHEN
        if new_status == OrderStatus.IN_KITCHEN and order.status == OrderStatus.PLACED:
            pass # Valid
        elif new_status == OrderStatus.SERVED and order.status in [OrderStatus.PLACED, OrderStatus.IN_KITCHEN]:
            pass # Valid
        else:
             raise ValidationError(f"Invalid status transition from {order.status} to {new_status}")

        order.status = new_status
        order.save()
        return order
    
    @staticmethod
    def add_items_to_order(order_id, items_data):
        order = Order.objects.get(id=order_id)
        # Check if Bill is pending
        if Bill.objects.filter(table=order.table, status=BillStatus.PENDING_PAYMENT).exists():
             raise ValidationError("Cannot add items after bill generated")
        
        if order.status == OrderStatus.COMPLETED or order.status == OrderStatus.CANCELLED:
             raise ValidationError("Cannot add items to closed order")

        total_items = 0
        for item in items_data:
            menu_item = MenuItem.objects.get(id=item['menu_item_id'])
            if not menu_item.is_available:
                raise ValidationError(f"Item {menu_item.name} is not available")
            
            # Check if item exists and aggregate
            existing_item = OrderItem.objects.filter(order=order, menu_item=menu_item).first()
            if existing_item:
                existing_item.quantity += item['quantity']
                existing_item.save()
            else:
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price_snapshot=menu_item.price
                )
            total_items += 1
            
        return order

class BillingService:
    @staticmethod
    @transaction.atomic
    def generate_bill(table_id):
        table = Table.objects.select_for_update().get(id=table_id)
        
        if table.status == TableStatus.AVAILABLE:
             raise ValidationError("Cannot generate bill for AVAILABLE table")
        
        active_order = table.active_order
        if not active_order:
             # Should not happen if OCCUPIED
             raise ValidationError("No active order found for table")

        # Check idempotency
        existing_bill = Bill.objects.filter(table=table, status=BillStatus.PENDING_PAYMENT).first()
        if existing_bill:
            return existing_bill

        # Calculate Total
        total = Decimal('0.00')
        for item in active_order.items.all():
            total += item.total_price

        # Tax logic can be added here
        
        bill = Bill.objects.create(
            table=table,
            total_amount=total,
            status=BillStatus.PENDING_PAYMENT
        )
        
        table.status = TableStatus.BILL_REQUESTED
        table.save()
        
        transaction.on_commit(lambda: TableService.broadcast_update(table_id))
        
        return bill

    @staticmethod
    @transaction.atomic
    def pay_bill(bill_id):
        bill = Bill.objects.select_for_update().get(id=bill_id)
        if bill.status == BillStatus.PAID:
            return bill # Idempotent
        
        bill.status = BillStatus.PAID
        bill.paid_at = timezone.now()
        bill.save()
        
        # Release Table
        table = bill.table
        table.status = TableStatus.AVAILABLE
        table.save()
        
        transaction.on_commit(lambda: TableService.broadcast_update(table.id))
        
        # Close Active Order
        active_order = table.active_order
        if active_order:
            active_order.status = OrderStatus.COMPLETED
            active_order.save()
        
        return bill

from django.utils import timezone
from datetime import datetime

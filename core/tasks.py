from celery import shared_task
from django.utils import timezone
import logging
from .models import Order, Bill, BillStatus, Table, TableStatus

logger = logging.getLogger(__name__)

@shared_task
def notify_kitchen(order_id):
    try:
        order = Order.objects.get(id=order_id)
        # In a real app, this might print to a kitchen printer or update a kitchen display
        # For this demo, we'll just log it
        print(f"KITCHEN NOTIFICATION: New Order #{order.id} for Table {order.table.table_number}")
        items = order.items.all()
        for item in items:
            print(f" - {item.quantity}x {item.menu_item.name}")
            
        return f"Notified kitchen for Order {order.id}"
    except Order.DoesNotExist:
        return "Order not found"

@shared_task
def check_pending_bills():
    """
    Checks for bills that have been PENDING_PAYMENT for more than 15 minutes.
    """
    threshold_time = timezone.now() - timezone.timedelta(minutes=15)
    long_pending_bills = Bill.objects.filter(
        status=BillStatus.PENDING_PAYMENT,
        created_at__lt=threshold_time
    )
    
    count = long_pending_bills.count()
    if count > 0:
        msg = f"MANAGER ALERT: {count} bills are pending for more than 15 minutes!"
        logger.warning(msg)
        return msg
    return "No long-pending bills found."

@shared_task
def auto_close_abandoned_tables():
    """
    Auto-close tables that have been occupied for more than 2 hours.
    """
    threshold_time = timezone.now() - timezone.timedelta(hours=2)
    abandoned_tables = Table.objects.filter(
        status=TableStatus.OCCUPIED,
        updated_at__lt=threshold_time
    )
    
    count = abandoned_tables.count()
    if count > 0:
        updated_count = abandoned_tables.update(status=TableStatus.CLOSED)
        
        # Broadcast updates for these tables (naive loop, fine for demo)
        from .services import TableService
        for t in abandoned_tables:
             TableService.broadcast_update(t.id)

        msg = f"AUTO-CLOSE: Closed {updated_count} abandoned tables."
        logger.info(msg)
        return msg
    return "No abandoned tables found."

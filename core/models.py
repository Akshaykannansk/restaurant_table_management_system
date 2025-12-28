from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class TableStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    OCCUPIED = 'OCCUPIED', 'Occupied'
    BILL_REQUESTED = 'BILL_REQUESTED', 'Bill Requested'
    CLOSED = 'CLOSED', 'Closed'

class OrderStatus(models.TextChoices):
    PLACED = 'PLACED', 'Placed'
    IN_KITCHEN = 'IN_KITCHEN', 'In Kitchen'
    SERVED = 'SERVED', 'Served'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class BillStatus(models.TextChoices):
    NOT_GENERATED = 'NOT_GENERATED', 'Not Generated'
    PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
    PAID = 'PAID', 'Paid'

class MenuItemCategory(models.TextChoices):
    STARTER = 'STARTER', 'Starter'
    MAIN = 'MAIN', 'Main'
    DRINKS = 'DRINKS', 'Drinks'
    DESSERT = 'DESSERT', 'Dessert'

class Table(models.Model):
    table_number = models.IntegerField(unique=True, validators=[MinValueValidator(1)])
    seating_capacity = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def active_order(self):
        # Return the most recent active order or None
        return self.orders.filter(status__in=['PLACED', 'IN_KITCHEN', 'SERVED']).last()

    def __str__(self):
        return f"Table {self.table_number}"

class MenuItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=MenuItemCategory.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.price})"

class Order(models.Model):
    table = models.ForeignKey(
        Table, 
        on_delete=models.CASCADE, 
        related_name='orders',
        null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PLACED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} for Table {self.table.table_number if self.table else 'N/A'}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of order

    def save(self, *args, **kwargs):
        if not self.price_snapshot:
            self.price_snapshot = self.menu_item.price
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return self.quantity * self.price_snapshot

class Bill(models.Model):
    table = models.ForeignKey(Table, on_delete=models.PROTECT)
    # Ideally link to Order or list of orders, but requirement says "Table" and "Bill".
    # Linking to Order is better for history, but requirement implies Table state.
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(
        max_length=20,
        choices=BillStatus.choices,
        default=BillStatus.NOT_GENERATED # Though usually created as PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Bill {self.id} - {self.status}"

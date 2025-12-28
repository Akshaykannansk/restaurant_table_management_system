from django.contrib import admin
from .models import Table, MenuItem, Order, Bill, OrderItem

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'seating_capacity', 'status')
    list_filter = ('status',)
    search_fields = ('table_number',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'total_amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')

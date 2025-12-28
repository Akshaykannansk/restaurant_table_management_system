from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.urls import reverse
from core.models import Table, MenuItem, MenuItemCategory, TableStatus, Order, OrderStatus, Bill, BillStatus, OrderItem
from core.services import TableService, OrderService, BillingService
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone

from django.utils.decorators import method_decorator
from core.permissions import role_required

class ManagerReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports.html'

    @method_decorator(role_required('Manager'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Revenue Today
        revenue = Bill.objects.filter(
            status=BillStatus.PAID,
            paid_at__date=today
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Bills Count
        bills_count = Bill.objects.filter(
            status=BillStatus.PAID,
            paid_at__date=today
        ).count()
        
        # Total Orders
        orders_count = Order.objects.filter(
            created_at__date=today
        ).count()
        
        # Top Items
        popular_items = OrderItem.objects.filter(
            order__created_at__date=today
        ).values('menu_item__name').annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(F('quantity') * F('price_snapshot'))
        ).order_by('-total_qty')[:5]

        context.update({
            'total_revenue_today': revenue,
            'paid_bills_count': bills_count,
            'total_orders_today': orders_count,
            'popular_items': popular_items
        })
        return context

class DashboardView(LoginRequiredMixin, ListView):
    model = Table
    template_name = 'dashboard.html'
    context_object_name = 'tables'
    ordering = ['table_number']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add summary metrics
        tables = context['tables']
        context['total_available'] = tables.filter(status=TableStatus.AVAILABLE).count()
        context['total_occupied'] = tables.filter(status__in=[TableStatus.OCCUPIED, TableStatus.CLOSED]).count()
        context['total_billing'] = tables.filter(status=TableStatus.BILL_REQUESTED).count()
        return context

class TableDetailView(LoginRequiredMixin, DetailView):
    model = Table
    template_name = 'table_detail.html'
    pk_url_kwarg = 'table_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = self.object
        active_order = table.active_order
        menu_items = MenuItem.objects.filter(is_available=True)
        
        menu_by_category = {}
        for cat in MenuItemCategory.values:
            menu_by_category[cat] = menu_items.filter(category=cat)

        context['active_order'] = active_order
        context['menu_by_category'] = menu_by_category
        context['bill'] = None

        if active_order and table.status == TableStatus.BILL_REQUESTED:
            context['bill'] = Bill.objects.filter(table=table, status=BillStatus.PENDING_PAYMENT).first()
            
        return context

@method_decorator(role_required('Waiter', 'Manager'), name='dispatch')
class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request, table_id):
        try:
            items_data = []
            for key, value in request.POST.items():
                if key.startswith('item_'):
                    item_id = int(key.split('_')[1])
                    quantity = int(value)
                    if quantity > 0:
                        items_data.append({'menu_item_id': item_id, 'quantity': quantity})
            
            if not items_data:
                messages.error(request, "Order must have at least one item.")
                return redirect('table_detail', table_id=table_id)

            OrderService.create_order(table_id, items_data)
            messages.success(request, "Order created successfully.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('table_detail', table_id=table_id)

@method_decorator(role_required('Waiter', 'Manager'), name='dispatch')
class AddItemsView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        try:
            items_data = []
            for key, value in request.POST.items():
                if key.startswith('item_'):
                    item_id = int(key.split('_')[1])
                    quantity = int(value)
                    if quantity > 0:
                        items_data.append({'menu_item_id': item_id, 'quantity': quantity})
            
            if items_data:
                OrderService.add_items_to_order(order_id, items_data)
                messages.success(request, "Items added to order.")
            else:
                messages.warning(request, "No items selected.")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
        return redirect('table_detail', table_id=order.table.id)

@method_decorator(role_required('Waiter', 'Manager'), name='dispatch')
class UpdateOrderStatusView(LoginRequiredMixin, View):
    def get(self, request, order_id, status):
        # Using GET for simplicity as per original implementation, 
        # though POST is better for state changes. Keeping API consistent.
        try:
            OrderService.update_order_status(order_id, status)
            messages.success(request, f"Order status updated to {status}")
        except Exception as e:
            messages.error(request, str(e))
        
        order = Order.objects.get(id=order_id)
        return redirect('table_detail', table_id=order.table.id)

@method_decorator(role_required('Cashier', 'Manager'), name='dispatch')
class GenerateBillView(LoginRequiredMixin, View):
    def post(self, request, table_id):
        try:
            BillingService.generate_bill(table_id)
            messages.success(request, "Bill generated.")
        except Exception as e:
            messages.error(request, str(e))
            
        return redirect('table_detail', table_id=table_id)

@method_decorator(role_required('Cashier', 'Manager'), name='dispatch')
class PayBillView(LoginRequiredMixin, View):
    def post(self, request, bill_id):
        try:
            bill = BillingService.pay_bill(bill_id)
            messages.success(request, "Bill paid. Table is now available.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('table_detail', table_id=Bill.objects.get(id=bill_id).table.id)

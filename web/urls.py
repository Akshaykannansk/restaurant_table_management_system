from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', views.ManagerReportView.as_view(), name='manager_reports'),
    path('table/<int:table_id>/', views.TableDetailView.as_view(), name='table_detail'),
    path('table/<int:table_id>/order/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('order/<int:order_id>/add/', views.AddItemsView.as_view(), name='add_items'),
    path('order/<int:order_id>/status/<str:status>/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('table/<int:table_id>/bill/generate/', views.GenerateBillView.as_view(), name='generate_bill'),
    path('bill/<int:bill_id>/pay/', views.PayBillView.as_view(), name='pay_bill'),
]

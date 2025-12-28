from django.test import Client, TestCase
from django.contrib.auth.models import User
from core.models import Table, MenuItem, MenuItemCategory, TableStatus, Order, OrderStatus, Bill, BillStatus
from core.management.commands.seed_data import Command as SeedCommand

class WorkflowTest(TestCase):
    def setUp(self):
        # Run seeding
        SeedCommand().handle()
        
        # Get users
        self.waiter = User.objects.get(username='waiter')
        self.cashier = User.objects.get(username='cashier')
        self.manager = User.objects.get(username='manager')
        
        self.client = Client()

    def test_full_flow(self):
        print("\n--- Starting Full Flow Test ---")
        
        # 1. Login as Waiter
        self.client.force_login(self.waiter)
        
        # 2. View Dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        print("Dashboard loaded.")

        # 3. Create Order for Table 1
        table = Table.objects.get(table_number=1)
        self.assertEqual(table.status, TableStatus.AVAILABLE)
        
        steak = MenuItem.objects.get(name='Steak')
        coke = MenuItem.objects.get(name='Coke')
        
        post_data = {
            f'item_{steak.id}': 2,
            f'item_{coke.id}': 2
        }
        
        response = self.client.post(f'/table/{table.id}/order/create/', post_data, follow=True)
        self.assertContains(response, "Order created successfully")
        
        table.refresh_from_db()
        self.assertEqual(table.status, TableStatus.OCCUPIED)
        print("Order created. Table Occupied.")
        
        # 4. Notify Kitchen (Implicitly tested by view, but we verify state)
        order = table.active_order
        self.assertEqual(order.status, OrderStatus.PLACED)
        
        # 5. Send to Kitchen
        self.client.get(f'/order/{order.id}/status/IN_KITCHEN/', follow=True)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.IN_KITCHEN)
        print("Order in Kitchen.")
        
        # 6. Serve Order
        self.client.get(f'/order/{order.id}/status/SERVED/', follow=True)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.SERVED)
        print("Order Served.")
        
        # 7. Add Items (Dessert)
        ice_cream = MenuItem.objects.get(name='Ice Cream')
        response = self.client.post(f'/order/{order.id}/add/', {f'item_{ice_cream.id}': 1}, follow=True)
        self.assertContains(response, "Items added to order")
        self.assertEqual(order.items.count(), 3) # Steak, Coke, Ice Cream
        print("Items added.")

        # 8. Generate Bill (Attempt as Waiter -> Should Fail)
        # Login as Waiter again
        self.client.logout()
        self.client.force_login(self.waiter)
        response = self.client.post(f'/table/{table.id}/bill/generate/', follow=True)
        self.assertEqual(response.status_code, 403)
        print("RBAC Verified: Waiter cannot generate bill.")

        # Generate as Cashier
        self.client.logout()
        self.client.force_login(self.cashier)
        
        response = self.client.post(f'/table/{table.id}/bill/generate/', follow=True)
        self.assertContains(response, "Bill generated")
        
        table.refresh_from_db()
        self.assertEqual(table.status, TableStatus.BILL_REQUESTED)
        bill = Bill.objects.get(table=table, status=BillStatus.PENDING_PAYMENT)
        self.assertTrue(bill.total_amount > 0)
        print(f"Bill Generated: ${bill.total_amount}")
        
        # 9. Pay Bill
        response = self.client.post(f'/bill/{bill.id}/pay/', follow=True)
        self.assertContains(response, "Bill paid")
        
        table.refresh_from_db()
        self.assertEqual(table.status, TableStatus.AVAILABLE)
        
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        
        print("Bill Paid. Table Available. Order Completed.")
        print("--- Test Passed Successfully ---")

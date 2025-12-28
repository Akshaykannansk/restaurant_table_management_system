from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from core.models import Table, MenuItem, MenuItemCategory, TableStatus
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds initial data for the Restaurant System'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Groups & Users
        groups = ['Manager', 'Waiter', 'Cashier']
        for g in groups:
            group, _ = Group.objects.get_or_create(name=g)
            user, created = User.objects.get_or_create(username=g.lower())
            if created:
                user.set_password('password123')
            
            # Ensure proper groups and permissions even if not created
            user.groups.add(group)
            if g == 'Manager':
                user.is_staff = True
                user.is_superuser = True # Optional: gives full access
            user.save()
            
            self.stdout.write(f"Updated user {g.lower()} / password123")

        # 2. Tables
        for i in range(1, 11):
            Table.objects.get_or_create(
                table_number=i,
                defaults={'seating_capacity': 4 if i <= 6 else 6}
            )
        self.stdout.write("Created 10 tables")

        # 3. Menu Items
        menu_items = [
            # Starters
            {'name': 'Garlic Bread', 'category': MenuItemCategory.STARTER, 'price': '5.00'},
            {'name': 'Soup', 'category': MenuItemCategory.STARTER, 'price': '6.50'},
            # Mains
            {'name': 'Steak', 'category': MenuItemCategory.MAIN, 'price': '25.00'},
            {'name': 'Pasta', 'category': MenuItemCategory.MAIN, 'price': '15.00'},
            {'name': 'Burger', 'category': MenuItemCategory.MAIN, 'price': '12.00'},
            # Drinks
            {'name': 'Coke', 'category': MenuItemCategory.DRINKS, 'price': '3.00'},
            {'name': 'Water', 'category': MenuItemCategory.DRINKS, 'price': '2.00'},
            # Desserts
            {'name': 'Ice Cream', 'category': MenuItemCategory.DESSERT, 'price': '5.00'},
            {'name': 'Cake', 'category': MenuItemCategory.DESSERT, 'price': '6.00'},
        ]

        for item in menu_items:
            MenuItem.objects.get_or_create(
                name=item['name'],
                defaults={
                    'category': item['category'],
                    'price': Decimal(item['price'])
                }
            )
        self.stdout.write("Created Menu Items")

        self.stdout.write(self.style.SUCCESS('Data seeding complete!'))

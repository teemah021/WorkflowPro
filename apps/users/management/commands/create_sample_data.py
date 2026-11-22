"""
Quick start script to create sample data for testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.requests.models import Request
from core.constants import UserRole, RequestState

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create users
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin.set_password('admin123')
        admin.save()
        
        manager, _ = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@example.com',
                'role': UserRole.MANAGER
            }
        )
        manager.set_password('manager123')
        manager.save()
        
        user, _ = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@example.com',
                'role': UserRole.USER
            }
        )
        user.set_password('user123')
        user.save()
        
        # Create sample requests
        for i in range(3):
            Request.objects.get_or_create(
                title=f'Sample Request {i+1}',
                defaults={
                    'description': f'This is a sample request for testing purposes.',
                    'creator': user,
                    'status': RequestState.DRAFT
                }
            )
        
        # Create submitted request
        Request.objects.get_or_create(
            title='Budget Approval Request',
            defaults={
                'description': 'Need approval for Q1 budget allocation.',
                'creator': user,
                'status': RequestState.SUBMITTED,
                'assigned_to': manager
            }
        )
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('Users created:')
        self.stdout.write(f'  - admin (password: admin123)')
        self.stdout.write(f'  - manager (password: manager123)')
        self.stdout.write(f'  - user (password: user123)')

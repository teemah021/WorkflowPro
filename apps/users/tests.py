"""
Tests for User model and authentication.
"""
from django.test import TestCase
from apps.users.models import User
from core.constants import UserRole


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=UserRole.USER
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, UserRole.USER)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_role_properties(self):
        """Test user role property methods"""
        admin = User.objects.create_user(
            username='admin',
            password='admin123',
            role=UserRole.ADMIN
        )
        manager = User.objects.create_user(
            username='manager',
            password='manager123',
            role=UserRole.MANAGER
        )
        user = User.objects.create_user(
            username='user',
            password='user123',
            role=UserRole.USER
        )
        
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_manager)
        self.assertTrue(admin.can_approve_requests())
        
        self.assertFalse(manager.is_admin)
        self.assertTrue(manager.is_manager)
        self.assertTrue(manager.can_approve_requests())
        
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_manager)
        self.assertTrue(user.is_regular_user)
        self.assertFalse(user.can_approve_requests())
    
    def test_soft_delete(self):
        """Test soft delete functionality"""
        user = User.objects.create_user(
            username='deletetest',
            password='test123'
        )
        
        user.delete()
        self.assertTrue(user.is_deleted)
        
        # User still exists in database
        deleted_user = User.objects.get(username='deletetest')
        self.assertTrue(deleted_user.is_deleted)

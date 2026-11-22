"""
Tests for Request model and state transitions.
"""
from django.test import TestCase
from django.utils import timezone
from apps.users.models import User
from apps.requests.models import Request
from core.constants import RequestState, UserRole
from core.exceptions import InvalidStateTransitionError


class RequestModelTest(TestCase):
    """Test cases for Request model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role=UserRole.USER
        )
        self.manager = User.objects.create_user(
            username='manager',
            password='manager123',
            role=UserRole.MANAGER
        )
    
    def test_create_request(self):
        """Test creating a request"""
        request = Request.objects.create(
            title='Test Request',
            description='Test description',
            creator=self.user
        )
        
        self.assertEqual(request.title, 'Test Request')
        self.assertEqual(request.status, RequestState.DRAFT)
        self.assertEqual(request.creator, self.user)
        self.assertFalse(request.is_deleted)
    
    def test_valid_state_transitions(self):
        """Test valid state transitions"""
        request = Request.objects.create(
            title='Test Request',
            description='Test description',
            creator=self.user,
            status=RequestState.DRAFT
        )
        
        # Draft -> Submitted
        self.assertTrue(request.can_transition_to(RequestState.SUBMITTED))
        request.submit()
        self.assertEqual(request.status, RequestState.SUBMITTED)
        
        # Submitted -> Approved
        self.assertTrue(request.can_transition_to(RequestState.APPROVED))
        request.approve(self.manager)
        self.assertEqual(request.status, RequestState.APPROVED)
        self.assertEqual(request.reviewed_by, self.manager)
        self.assertIsNotNone(request.reviewed_at)
    
    def test_invalid_state_transitions(self):
        """Test invalid state transitions"""
        request = Request.objects.create(
            title='Test Request',
            description='Test description',
            creator=self.user,
            status=RequestState.DRAFT
        )
        
        # Cannot go from Draft to Approved directly
        self.assertFalse(request.can_transition_to(RequestState.APPROVED))
        
        with self.assertRaises(InvalidStateTransitionError):
            request.transition_to(RequestState.APPROVED)
    
    def test_terminal_states(self):
        """Test that terminal states cannot transition"""
        request = Request.objects.create(
            title='Test Request',
            description='Test description',
            creator=self.user,
            status=RequestState.APPROVED
        )
        
        self.assertTrue(request.is_terminal_state())
        self.assertFalse(request.can_transition_to(RequestState.SUBMITTED))
        self.assertFalse(request.can_transition_to(RequestState.REJECTED))
    
    def test_rejection_with_reason(self):
        """Test rejecting a request with a reason"""
        request = Request.objects.create(
            title='Test Request',
            description='Test description',
            creator=self.user,
            status=RequestState.SUBMITTED
        )
        
        reason = 'Invalid request format'
        request.reject(self.manager, reason)
        
        self.assertEqual(request.status, RequestState.REJECTED)
        self.assertEqual(request.rejection_reason, reason)
        self.assertEqual(request.reviewed_by, self.manager)
    
    def test_request_editable_only_in_draft(self):
        """Test that requests are only editable in draft state"""
        draft_request = Request.objects.create(
            title='Draft Request',
            description='Test',
            creator=self.user,
            status=RequestState.DRAFT
        )
        
        submitted_request = Request.objects.create(
            title='Submitted Request',
            description='Test',
            creator=self.user,
            status=RequestState.SUBMITTED
        )
        
        self.assertTrue(draft_request.is_editable())
        self.assertFalse(submitted_request.is_editable())
    
    def test_soft_delete(self):
        """Test soft delete functionality"""
        request = Request.objects.create(
            title='Test Request',
            description='Test',
            creator=self.user
        )
        
        request.delete()
        self.assertTrue(request.is_deleted)
        
        # Request still exists in database
        deleted_request = Request.objects.get(id=request.id)
        self.assertTrue(deleted_request.is_deleted)

"""
Custom middleware for the approval system.
"""
from django.utils.deprecation import MiddlewareMixin
from apps.audit_logs.models import AuditLog
from core.constants import AuditAction


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log certain actions.
    """
    
    def process_request(self, request):
        """Store request start time"""
        import time
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log completed requests"""
        # Only log authenticated requests
        if not request.user.is_authenticated:
            return response
        
        # Only log state-changing methods
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return response
        
        # Calculate request duration
        if hasattr(request, '_start_time'):
            import time
            duration = time.time() - request._start_time
        else:
            duration = 0
        
        # You can add more specific logging logic here
        
        return response

# permissions.py
from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """Permission to allow only Admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')
from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.memberships.filter(role__role_name='Admin').exists()

class IsAccountMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        account_id = view.kwargs.get('account_id') or request.data.get('account')
        if not account_id:
            return True  # Allow listing or actions not tied to a specific account
        membership = request.user.memberships.filter(account_id=account_id).first()
        if not membership:
            return False
        if request.method in ['POST', 'DELETE']:
            return membership.role.role_name == 'Admin'
        return True
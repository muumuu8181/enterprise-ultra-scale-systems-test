from rest_framework import permissions
from core.models import User

class HasClearance(permissions.BasePermission):
    """
    Custom permission to check if user has sufficient clearance level.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # If the object doesn't have a required_clearance attribute, allow access
        if not hasattr(obj, 'required_clearance'):
            return True

        user_rank = request.user.get_clearance_rank()
        req_rank = User.get_clearance_rank_for_level(obj.required_clearance)

        return user_rank >= req_rank

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def is_manager(user):
    """Manager = staff atau pengguna dengan role 'admin'."""
    return user.is_staff or getattr(user, 'role', None) == 'admin'


def manager_required(view_func):
    """Batasi akses view hanya untuk staff/admin.

    - Pengguna anonim: dialihkan ke halaman login.
    - Pengguna login biasa: mendapat 403.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_manager(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped)

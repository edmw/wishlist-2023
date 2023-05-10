"""Model representations in admin site."""
from django.conf import settings as django_settings

# Import admin models in supporting environments:
if django_settings.ENVIRONMENT_SUPPORTS_ADMIN:
    from .favorite import FavoriteAdmin
    from .reservation import ReservationAdmin
    from .user import UserAdmin
    from .user_settings import UserSettings
    from .wish import WishAdmin
    from .wishlist import WishlistAdmin

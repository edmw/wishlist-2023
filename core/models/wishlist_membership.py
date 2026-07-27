from __future__ import annotations

from typing import Any, Iterable, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.base import ModelBase

from core.models import fields, types
from core.models._base import IDMixin
from core.models.types import Visibility


class WishlistMembership(IDMixin[types.WishlistMembershipID], models.Model):
    """Model used to represent a user’s collaboration role on a wishlist."""

    id_type = types.WishlistMembershipID
    id_field = fields.WishlistMembershipIDField()

    wishlist = models.ForeignKey(
        "Wishlist",
        on_delete=models.CASCADE,
        related_name="collaboration_memberships",
    )
    wishlist_id: types.WishlistID

    user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="wishlist_memberships",
    )
    user_id: types.UserID

    role_field = models.CharField(
        max_length=types.WishlistMembershipRole.max_length,
        choices=types.WishlistMembershipRole.choices,
        default=types.WishlistMembershipRole.default,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wishlist Membership"
        verbose_name_plural = "Wishlist Memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "user"],
                name="wishlist_membership_unique_wishlist_user",
            ),
        ]

    class Fields:
        ID = "id_field"
        WISHLIST = "wishlist"
        USER = "user"
        ROLE = "role_field"
        CREATED_AT = "created_at"
        MODIFIED_AT = "modified_at"

    # Concerns

    def __str__(self) -> str:
        """Returns a string representation of this wishlist membership.

        Returns:
            Representation text.
        """
        return f"{self.user_id} -> {self.wishlist_id}"

    def __repr__(self) -> str:
        """Returns a string reputation of this wishlist membership.

        Returns:
            Reputation text.
        """
        return (
            f"<{self.__class__.__name__}[{str(self.id)}]: "
            f"wishlist={self.wishlist_id}; user={self.user_id}; role={self.role}>"
        )

    @override
    def save(
        self,
        *args: Any,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.full_clean()
        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

    # Custom properties

    @property
    def role(self) -> types.WishlistMembershipRole:
        return types.WishlistMembershipRole(self.role_field)

    @role.setter
    def role(self, role: types.WishlistMembershipRole) -> None:
        self.role_field = role

    def clean(self) -> None:
        super().clean()

        if self.user_id and self.wishlist_id and self.wishlist.owner_id == self.user_id:
            raise ValidationError("Wishlist owner cannot be added as collaborator.")

        if self.wishlist.visibility == Visibility.PRIVATE:
            raise ValidationError("Private wish lists cannot have collaborators.")

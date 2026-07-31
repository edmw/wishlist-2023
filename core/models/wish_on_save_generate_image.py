import logging
from typing import Any, Iterable, Protocol, cast

from django.db import transaction
from django.db.models.base import ModelBase

from core.models._typing import HasModelState, HasPrimaryKey, IsSaveable

logger = logging.getLogger(__name__)


class ModelSupportsSave(HasPrimaryKey, HasModelState, Protocol):
    pass


class OnSaveGenerateImageMixin(IsSaveable):
    def save(
        self: ModelSupportsSave,
        *args: Any,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        from .wish import Wish

        wish = cast(Wish, self)
        created = self._state.adding
        if created:
            updated_reference_photo = wish.reference_photo
        else:
            try:
                before = Wish.objects.get(pk=wish.id)
                # update
                if before.reference_photo != wish.reference_photo:
                    updated_reference_photo = wish.reference_photo
                else:
                    updated_reference_photo = None
            except Wish.DoesNotExist:
                # create
                updated_reference_photo = wish.reference_photo

        if updated_reference_photo:
            wish.image_field.delete(save=False)
            if update_fields is not None:
                update_fields = {Wish.Fields.IMAGE}.union(update_fields)

        super().save(
            *args,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
            **kwargs,
        )

        if updated_reference_photo:
            from core.tasks.wish import generate_image_from_reference_photo

            wish_id = wish.id
            transaction.on_commit(
                lambda: generate_image_from_reference_photo.apply_async(
                    kwargs={
                        "wish_id": wish_id,
                    },
                    countdown=0.1,
                ),
                using=using,
            )

# 1000. Wishlist collaboration membership model

Date: 2026-07-21

## Status

Accepted

## Context

We want to add collaboration to wishlists. A wishlist must keep exactly one owner, may have zero to many collaborators, and collaboration roles may grow in the future. Collaboration must not be possible for private wishlists. Editors must be able to do all wish-level actions, but must not be able to delete a wishlist or change wishlist settings. In the first step, there is no UI for managing collaborators, so collaboration must be testable via a management command.

## Decision

We model collaboration with a dedicated membership relation between wishlist and user, including a role field.

The owner remains the single source of truth in Wishlist.owner and is not duplicated in memberships.

Membership constraints and invariants:

- Unique membership per wishlist and user (unique constraint on wishlist + user).
- Owner cannot be added as a membership on the same wishlist.
- Private wishlist invariant: private wishlists cannot have memberships.
- Visibility downgrade block: changing visibility to private is rejected while memberships exist.

Authorization split:

- Editors can perform all wish-level actions on collaborated lists.
- Editors cannot delete lists.
- Editors cannot change list settings.

Listing behavior:

- "Deine Wunschzettel" is a single combined list of owned and collaborated wishlists.
- Collaborated wishlists are explicitly marked.
- The personal wishlist counter includes both owned and collaborated wishlists.
- Sorting stays uniform with existing listing behavior.

Management command for step one:

- Explicit operations: add-editor and remove-editor (no toggle semantics).
- Targeting: wishlist by wishlist ID; user by user ID or email resolving to exactly one user.
- Operations are idempotent: adding an existing membership and removing a missing membership are both successful no-ops.

## Consequences

This keeps ownership simple and stable while enabling role-based collaboration growth. Permission checks become explicit at wishlist-level versus wish-level boundaries. The private visibility invariant is enforced strictly and predictably. The management command enables immediate integration testing before introducing any collaboration UI.

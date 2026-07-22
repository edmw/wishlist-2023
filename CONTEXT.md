# Wishlist

Domain model for wish lists, wishes, and collaboration roles between users.
It defines canonical language for permissions and ownership semantics.

## Language

**Wishlist Owner**:
The single user referenced by a wishlist’s `owner` field and the only source of truth for ownership.
_Avoid_: Owner membership, primary collaborator

**Private Wishlist Invariant**:
A wishlist with private visibility cannot have any collaboration memberships.
_Avoid_: Private with collaborators, implicit exceptions

**Visibility Downgrade Block**:
Changing a wishlist to private is rejected while collaboration memberships exist.
_Avoid_: Silent collaborator removal, automatic cleanup on downgrade

**Wishlist Membership**:
A relationship between a user and a wishlist that grants a specific role in collaboration.
_Avoid_: Collaboration user, participant mapping

**Membership Role**:
The capability level a member has on a wishlist, represented by a named role such as `editor`.
_Avoid_: Permission flag, mode

**Editor Capability**:
An editor can perform all wish-level actions on a collaborated wishlist but cannot delete the wishlist or change wishlist settings.
_Avoid_: Partial editor, settings editor

**Personal Wishlist Index**:
The "Deine Wunschzettel" list combines owned and collaborated wishlists in one unified listing.
_Avoid_: Owner-only list, split ownership sections

**Collaboration Marker**:
Collaborated wishlists are explicitly labeled in the personal index to distinguish them from owned wishlists.
_Avoid_: Unmarked collaboration, implicit ownership assumptions

**Unified Wishlist Count**:
The personal wishlist counter includes both owned and collaborated wishlists.
_Avoid_: Owner-only count

**Collaboration Command Targeting**:
Collaboration management addresses wishlists by wishlist ID and users by user ID or email resolved to exactly one user.
_Avoid_: Name-based targeting, ambiguous user lookup

**Explicit Collaboration Commands**:
Collaboration is managed with explicit add and remove operations instead of toggle semantics.
_Avoid_: Toggle editor command

**Idempotent Collaboration Mutation**:
Adding an existing membership or removing a missing membership succeeds without error.
_Avoid_: State-dependent failure for no-op operations

**Owner-Membership Exclusion**:
The wishlist owner cannot be stored as a collaboration membership on the same wishlist.
_Avoid_: Owner as editor, mirrored owner membership

**Single Membership Constraint**:
At most one collaboration membership exists per pair of wishlist and user.
_Avoid_: Duplicate memberships, parallel role rows

**Deletion Collaboration Warning**:
When deleting a collaborated wishlist, the warning states the number of editors but does not identify them by name.
_Avoid_: Unqualified collaboration warning, editor name disclosure in delete flow

**Combined Deletion Warning Block**:
If a wishlist has wishes and editors, both deletion risks are shown together in one warning block while the name confirmation remains tied only to existing wishes.
_Avoid_: Collapsed single-risk wording, confirmation tied to editor presence alone

**Pluralized Editor Warning**:
The deletion warning distinguishes between one editor and multiple editors.
_Avoid_: Flat editor-count wording

**Explicit Access-Loss Deletion Warning**:
The deletion warning states explicitly that editors lose access when the wishlist is deleted.
_Avoid_: Abstract collaboration warning without consequence

**View-Service Persistence Boundary**:
Views do not execute model or database-related logic directly, including relation counts; all such logic is delegated to service calls.
_Avoid_: Direct queryset or related-manager access in views for business data

**Membership Count Semantics**:
Deletion warnings use a role-agnostic membership count (`count_memberships`) because membership type does not change delete-risk communication.
_Avoid_: Role-specific counting for delete warnings

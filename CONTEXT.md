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

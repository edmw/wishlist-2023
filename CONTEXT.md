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

**Lens-Based Read Convention**:
Read-side collaboration queries in services are composed through a membership lens instead of direct model manager/queryset access.
_Avoid_: Inline read queries on membership model classes inside services

**Editor-Only Membership Filter**:
Membership selection for edit capability is role-based via an explicit `editors_only` filter.
_Avoid_: Capability-named lens filters that blur data selection and policy interpretation

**Composable Membership Lens Filters**:
Membership reads are composed from `by_wishlist`, `by_user`, and `editors_only` as needed per service use case.
_Avoid_: Single-purpose combined filters that hide query intent

**Lens Scope-Building Boundary**:
Lens methods using `by_`, `without_`, `for_`, and ordering names only narrow or shape scope and never execute queries.
_Avoid_: Scope methods that materialize or count results

**Lens Terminal Operation Boundary**:
Lens terminal methods execute queries (`count`, `exists`, `one`, `first_or_none`) while `qs` only exposes the current scope without executing.
_Avoid_: Direct `queryset` access in service read paths

**Consumed Lens After Terminal**:
After any terminal lens operation, the lens instance is consumed and must not be narrowed or reshaped further.
_Avoid_: Reusing the same lens instance for additional scope changes after terminal execution

**Single-Use Terminal Lens Instance**:
Once a terminal operation is executed, no further operations are allowed on that lens instance, including additional terminal calls.
_Avoid_: Chaining multiple terminal reads on one consumed lens instance

**Non-Consuming Queryset Escape Hatch**:
`qs()` exposes the current scope without consuming the lens instance, but it is unavailable once the lens is consumed by a terminal operation.
_Avoid_: Treating `qs()` as terminal while also reusing consumed lens instances

**Explicit Consumed-Lens Error**:
Operations on a consumed lens fail with a dedicated consumed-state error derived from lens state errors.
_Avoid_: Reusing unrelated state-conflict errors for consumed-lens violations

**Central Consumption Guard**:
Consumption checks are centralized in LensBase and are required at the start of every scope-building method.
_Avoid_: Ad-hoc per-lens consumption checks that can drift over time

**Owner-Scoped Membership Overview**:
The membership overview for a wishlist belongs to owner-level management and is accessible only to the wishlist owner.
_Avoid_: Editor-visible membership administration, collaborator-owned membership view

**Conditional Membership Action**:
The memberships action in the personal wishlist index appears only when the wishlist currently has at least one collaboration membership.
_Avoid_: Always-visible membership action, count-independent action visibility

**Icon-Only Membership Action**:
The memberships action in list rows is represented by a standalone icon button without an inline membership count.
_Avoid_: Count-labeled membership action, mixed icon-text action in row controls

**Owner-Managed Membership Removal**:
The memberships overview includes an owner-only remove action per membership row that opens a dedicated confirmation step before deletion.
_Avoid_: Collaborator-managed membership deletion, direct deletion without confirmation

**Membership Empty-State Fallback**:
The memberships overview has a dedicated empty state when no memberships remain at render time.
_Avoid_: Missing empty handling, forced redirect on empty membership set

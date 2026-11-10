# 1001. Wishlist invitations

Date: 2026-11-10

## Status

Accepted

The functional rules (variants, state machine, access mode, deadlines, limits) are specified in [req-0002](./req-0002-wishlist-invitations.md). This ADR describes the underlying architecture.

## Context

A user should be able to invite one or more other persons to participate. Reasons for this are to make someone aware of a wish list in the first place or to invite a person to contribute to a wish list (editor).

The architecture must:

* allow multiple concrete invitation types without duplicating the shared behavior,
* decouple creating from sending,
* model the lifecycle of an invitation explicitly and traceably,
* fulfill the requirements of req-0002 regarding token security, identity verification and avoidance of information leaks,
* allow delivery through exchangeable channels.

Sign-in and registration are only possible via OIDC (Google). The e-mail address and its verification status come from the identity provider.

## Decision

A general **model** of an invitation is extended for concrete occasions to specific invitation types. A concrete model handles offering and accepting of invitations to a specific wish list. A **service** offers functionality to create, send, accept, decline and revoke invitations. **Views** handle the interaction of the recipient (invitation page, accept, decline, explicit consent to the editor role).

### Models

The abstract base class `Invitation` holds the following fields:

* `token_hash` -- hash of the randomly generated, unguessable token. The token itself is not stored; it only exists in the link of the mail.
* `email` -- normalized e-mail address of the recipient (lowercase, trimmed, no alias normalization).
* `state` -- one of `CREATED`, `PENDING`, `ACCEPTED`, `DECLINED`, `EXPIRED`, `REVOKED`.
* `created_at` -- time at which the invitation was created.
* `sent_at` -- time at which the invitation was handed over to the mail delivery.
* `resolved_at` -- time of the transition into a final state.
* `inviter` -- the user who issued the invitation.

Specialized invitation types must implement:

* `expires_at`, or a rule defining when a sent invitation expires. The mixin `ExpiresAfterFixedTime` implements this as a fixed, configurable period after creation (default 10 days).
* `was_accepted` -- performs the type-specific actions after the invitation was accepted.

### Lifecycle

The state is changed exclusively by the service. Allowed transitions:

* `CREATED` → `PENDING` after successful handover of the mail to the mail delivery
* `CREATED`/`PENDING` → `REVOKED` (system only)
* `PENDING` → `ACCEPTED`
* `PENDING` → `DECLINED`
* `PENDING` → `EXPIRED`

`ACCEPTED`, `DECLINED`, `EXPIRED` and `REVOKED` are final states. Any action on an invitation in a final state does not change its state. Expiry is set by a periodic job and additionally checked on access, so that an expired invitation can never be accepted even if the job has not run yet.

Revocation is done by the system only, not manually by the owner. Triggers are setting the wish list to PRIVATE and replacement by a new invitation for the same wish list and address.

### InvitationService

The `InvitationService` is the only place that processes invitations:

* `create_*` -- creates an invitation in state `CREATED`, checks authorization, visibility and access mode (see Wishlist invitations) as well as the daily limit, and revokes an existing `PENDING` invitation for the same wish list and address. Creating and revoking happen in a single transaction.
* `send_invitation` -- builds the message and hands it over to a transport adapter. After successful handover, the invitation becomes `PENDING`.
* `accept_invitation` -- checks, at the time of acceptance, the state, expiry, match of the verified e-mail address and the current visibility of the wish list. Only then `was_accepted` is called. Acceptance is atomic so that the token can only be used once, even with concurrent calls.
* `decline_invitation` -- sets `DECLINED` without side effects on favorites or editors.
* `revoke_open_invitations(wishlist)` -- revokes all `CREATED`/`PENDING` invitations of a wish list; called when the wish list is set to PRIVATE.
* `expire_invitations` -- sets expired `PENDING` invitations to `EXPIRED`.

The caller of `accept_invitation` passes the identity of the signed-in user including the verification status of the e-mail address; the authorization check lies within the service, not with the caller.

### Token and links

* The token is generated randomly and cryptographically secure, only its hash is stored, and the token is contained in the link of the mail.
* Lookup is done via the hash of the presented token.
* Unknown, expired, already used, revoked and declined tokens lead to an identical response. No details are revealed.
* An invitation can only be accepted by a person with a verified, matching e-mail address. Opening the link alone does not change the state; accepting and declining are explicit actions on the invitation page.
* Without sign-in, the invitation page only shows that an invitation exists and requests to sign in. The title or other content of the wish list is not shown.

### Transport

The delivery channel is not part of the model hierarchy. Sending is performed by the service through transport adapters, so that additional channels can be added without introducing new invitation model types. The initial adapter sends e-mails.

The message contains only structured content (title of the wish list, name of the owner, variant, personal link) and no free text. The language is that of the owner (browser or profile), falling back to English. Delivery errors and bounces are not handled.

### WishlistInvitation

`WishlistInvitation` implements `Invitation` directly and adds:

* `wishlist` -- reference to exactly one wish list.
* `variant` -- `NOTIFY` or `EDITOR`.

Semantics of the variants:

* `NOTIFY`: Accepting adds the wish list to the recipient's favorites.
* `EDITOR`: Accepting additionally makes the recipient an editor. The editor role is only granted after a separate, explicit consent; opening the link does not imply it. The owner can never become editor of his own wish list; this is checked on acceptance regardless of how the invitation was created.

An invitation does not grant access. Access is solely determined by the visibility of the wish list. There is no ACL.

Rules regarding visibility:

* No invitations can be created for PRIVATE wish lists; the user interface does not offer the function and the backend rejects the request.
* Visibility is additionally checked at the time of acceptance. If the wish list is PRIVATE at that moment, acceptance fails with an error and neither a favorite nor the editor role is created.
* Changes between PUBLIC and USERS leave open invitations valid.
* When setting a wish list to PRIVATE, open invitations are revoked. Setting to PRIVATE remains only possible without editors (existing behavior).

Rules regarding the application access mode:

* `PUBLIC`: Unregistered recipients can register and then accept.
* `EXISTING`: Registration through an invitation is only possible if a configuration switch (default: off) allows it, and then only with the verified address of the invitation. Already registered users can sign in and accept.
* `NOBODY`: Creating and accepting are not possible. Open invitations remain `PENDING`, expire regularly and are not revoked by the mode change.

Registration and acceptance of the editor role are separate steps in this order.

### Abuse protection and privacy

* The number of invitations created per owner and day is limited (configurable, default 30). Every created invitation counts, including replacements and resends. When the limit is exceeded, the request is rejected and no mail is sent.
* The system does not check whether the recipient already has the wish list as favorite or is already an editor, and does not reveal this to the owner.
* The owner is not informed whether and how a recipient reacted. There is no status display of invitations for the owner.

### Creating and sending

Creating and sending are a two-step process: `create_*` creates the invitation as `CREATED`, `send_invitation` hands it over to the transport. An invitation that was created but not yet sent can thus be sent later. In the normal case (wish list invitation by the owner), the caller invokes both steps immediately one after the other.

## Consequences

* New invitation types and new delivery channels can be added without changing existing models.
* All business logic (state transitions, checks, limits) lies in the service and is centrally testable. Views and models contain no transition rules of their own.
* Since only the token hash is stored, the link of an invitation cannot be reconstructed. Resending therefore always creates a new invitation that replaces the previous `PENDING` one (and counts towards the daily limit).
* Being able to revoke open invitations is the prerequisite for making a wish list private again. Accepted invitations do not block this; the only decisive rule remains the existing one that a wish list with editors cannot be set to PRIVATE.
* The state `EXPIRED` requires a periodic job as well as a check at access time.
* Delivery status is not tracked; `PENDING` only means that the message was handed over to the mail delivery, not that it reached the recipient.
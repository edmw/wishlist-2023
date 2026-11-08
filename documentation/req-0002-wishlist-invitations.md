# 2. Wishlist invitations

Date: 2026-11-08

## Status

Proposed

## Context

Wishlists have a visibility (PUBLIC, USERS, PRIVATE). The visibility is the
only access level, there is no ACL. The application has an access mode
(NOBODY, EXISTING, PUBLIC). Besides the owner, a wishlist can have editors.
Today, the editor relation can only be established with an administrative
command.

Invitations replace this administrative command and additionally allow an
owner to make a wishlist known to other people.

An invitation refers to exactly one wishlist and is sent by e-mail. It has
one of two variants:

* **Notify**: makes the wishlist known to the recipient. Accepting it adds
  the wishlist to the recipient's favorites.
* **Notify and editor**: additionally offers the recipient to become an
  editor. Accepting it adds the wishlist to the favorites and makes the
  recipient an editor.

An invitation does not grant access. Access is solely determined by the
visibility of the wishlist. Editor rights, their revocation and the rule
"a wishlist with editors cannot be set to PRIVATE" are already implemented
and are not part of this document.

Sign-in and registration are only possible via OIDC with Google. The e-mail
address of a user therefore comes from the identity provider.

## Terms

* **Owner**: user who owns the wishlist.
* **Recipient**: person addressed by the e-mail address of the invitation.
* **Variant NOTIFY**: invitation without editor offer.
* **Variant EDITOR**: invitation with editor offer.
* **Invalid link**: a link whose token is unknown, expired, already used,
  revoked or declined. All cases are treated identically towards the
  caller.

## Requirements

### Creating invitations

* REQ-2.1: Only the owner of a wishlist must be able to create invitations
  for it.
* REQ-2.2: An invitation must refer to exactly one wishlist and contain
  exactly one e-mail address and one variant (NOTIFY or EDITOR).
* REQ-2.3: The system must not allow invitations for wishlists with
  visibility PRIVATE. The user interface must not offer the function, and
  the backend must reject the request.
* REQ-2.4: The system must not allow invitations while the access mode is
  NOBODY. The owner must receive a clear error message.
* REQ-2.5: The owner must be able to invite his own e-mail address with
  variant NOTIFY.
* REQ-2.6: The system must not allow the owner to become editor of his own
  wishlist, regardless of how the invitation was created.
* REQ-2.7: The invitation must not contain free text.
* REQ-2.8: The number of invitations per owner and day must be limited.
  The limit must be configurable, default 30. Every created invitation
  counts, including replacements and resends.
* REQ-2.9: When the limit is exceeded, the system must reject further
  invitations with an error message and must not send mail.

### Replacing and resending

* REQ-2.10: When an invitation is created for the same wishlist and the
  same e-mail address while an earlier one is PENDING, the earlier one must
  become REVOKED and the new one replaces it.
* REQ-2.11: When an earlier invitation for the same wishlist and e-mail
  address is ACCEPTED, DECLINED, EXPIRED or REVOKED, a new invitation must
  be allowed without restriction other than REQ-2.8.
* REQ-2.12: The system must not check whether the recipient already has the
  wishlist as favorite or is already an editor, and must not reveal
  this to the owner.

### Mail

* REQ-2.13: The system must send the invitation to the given e-mail
  address.
* REQ-2.14: The mail must contain the title of the wishlist, the name of
  the owner (first and last name, otherwise username), the variant and the
  personal link.
* REQ-2.15: The mail language must be the language of the owner. If the
  owner has no language available (Google, browser or profile), English
  must be used.
* REQ-2.16: Delivery errors and bounces are not handled (see Out of Scope).

### Token and link

* REQ-2.17: Each invitation must have a random, unguessable token. The
  system must store only a hash of the token.
* REQ-2.18: The token must be usable exactly once and only by the person
  whose verified e-mail address matches the invitation address.
* REQ-2.19: The comparison of e-mail addresses must be case-insensitive on
  the normalized address, without alias handling (dots and `+` in the local
  part are not normalized).
* REQ-2.20: An invitation can only be accepted with an e-mail address that
  the identity provider marks as verified.
* REQ-2.21: When the link is opened without being signed in, the system
  must only show that an invitation exists and request to sign in. It must
  not show the title or any content of the wishlist.
* REQ-2.22: For an invalid link, the system must respond identically
  regardless of the reason and must not reveal any details.

### Lifecycle

* REQ-2.23: An invitation must have exactly one of the states CREATED,
  PENDING, ACCEPTED, DECLINED, EXPIRED, REVOKED.
* REQ-2.24: A new invitation starts as CREATED. After successful handover
  of the mail to the mail delivery, it becomes PENDING.
* REQ-2.25: A PENDING invitation must become EXPIRED 10 days after
  creation.
* REQ-2.26: ACCEPTED, DECLINED, EXPIRED and REVOKED are final states.
* REQ-2.27: REVOKED must only be set by the system. There is no manual
  revocation by the owner. Triggers are: the wishlist is set to PRIVATE
  (REQ-2.28) and replacement by a new invitation (REQ-2.10).

### Visibility changes

* REQ-2.28: When a wishlist is set to PRIVATE, all its PENDING (and
  CREATED) invitations must become REVOKED. This is only possible when the
  wishlist has no editors (already implemented).
* REQ-2.29: When a wishlist is set from PUBLIC to USER or from USER to
  PUBLIC, PENDING invitations must remain valid.
* REQ-2.30: The system must check the visibility of the wishlist at the
  moment of acceptance, not only at creation.
* REQ-2.31: When accepting an invitation for a wishlist that is PRIVATE at
  that moment, the system must show an error and must neither add a
  favorite nor make the recipient an editor.

### Accepting and declining

* REQ-2.32: A recipient who is signed in and whose verified address
  matches must be able to accept or decline a PENDING invitation.
* REQ-2.33: Accepting must add the wishlist to the favorites of the
  recipient.
* REQ-2.34: Accepting a variant EDITOR invitation must only make the
  recipient an editor after explicit consent. The consent must be a
  separate, active action. It must not be implied by opening the link.
* REQ-2.35: When the recipient accepts variant EDITOR but is the owner of
  the wishlist, the system must reject it (REQ-2.6).
* REQ-2.36: Declining must set the invitation to DECLINED and must not
  create a favorite or editor.
* REQ-2.37: The owner must not be informed whether and how a recipient
  accepted or declined.

### Access mode

* REQ-2.38: In access mode PUBLIC, an unregistered recipient must be able
  to register and then accept the invitation.
* REQ-2.39: In access mode EXISTING, an unregistered recipient must be able
  to register only if a configuration switch allows registration through
  invitations, and then only with the e-mail address of the invitation.
* REQ-2.40: The configuration switch of REQ-2.39 must be off by default.
* REQ-2.41: When registering through an invitation in EXISTING mode, the
  verified e-mail address from the identity provider must match the
  invitation address. Otherwise, registration must be rejected.
* REQ-2.42: In access mode NOBODY, accepting must not be possible. Open
  invitations remain PENDING and expire regularly. The change of the mode
  must not revoke them.
* REQ-2.43: A user who is already registered must be able to accept
  without registering again, in every access mode in which sign-in is
  possible.
* REQ-2.44: Becoming an editor is only possible for registered users.
  Registration and acceptance of the editor offer must be separate steps
  in this order.

## Acceptance Criteria

### Creating

* Given a wishlist with visibility USER, when the owner invites an address
  with variant NOTIFY, then an invitation in state PENDING exists and a
  mail was handed over.
* Given a wishlist with visibility PRIVATE, when the owner tries to
  invite, then the request is rejected and no invitation exists.
* Given a wishlist with visibility PRIVATE, when the owner opens the
  wishlist, then no invitation function is offered.
* Given a user who is not the owner, when he tries to invite for the
  wishlist, then the request is rejected.
* Given access mode NOBODY, when the owner tries to invite, then he gets
  an error message and no invitation exists.
* Given the owner, when he invites his own address with variant NOTIFY,
  then the invitation is created.
* Given the owner, when he invites his own address with variant EDITOR and
  accepts, then no editor relation is created and he gets an error.
* Given the owner has reached the daily limit, when he invites again, then
  the request is rejected and no mail is sent.
* Given the limit is configured to 5, when the owner creates the sixth
  invitation within a day, then it is rejected.

### Replacing and resending

* Given a PENDING invitation for address A and wishlist W, when the owner
  invites A for W again, then the old one is REVOKED and the new one is
  PENDING.
* Given a PENDING invitation for A and W, when the owner invites A again,
  then the old link becomes invalid.
* Given an ACCEPTED invitation for A and W, when the owner invites A
  again, then a new invitation is created and the system does not tell
  whether A already has the favorite.
* Given a DECLINED invitation for A and W, when the owner invites A again,
  then a new invitation is created.
* Given every kind of invitation creation, when counted, then replacements
  and resends are included in the daily limit.

### Mail

* Given an invitation, when the mail is created, then it contains the
  title, the owner name, the variant and the link, and no free text.
* Given an owner without first and last name, when the mail is created,
  then the username is used.
* Given an owner with language German, when the mail is created, then it
  is in German.
* Given an owner without any available language, when the mail is created,
  then it is in English.

### Token and link

* Given an invitation, when it is stored, then only the hash of the token
  is stored.
* Given a link that was already used, when it is opened again, then the
  response is the same as for an unknown token.
* Given a signed-in user with a different address than the invitation, when
  he opens the link, then he cannot accept and receives the response for an
  invalid link.
* Given an invitation to `Max@Example.com`, when `max@example.com` signs in
  with a verified address, then the addresses are considered equal.
* Given an invitation to `max@gmail.com`, when `m.ax@gmail.com` signs in,
  then the addresses are considered different.
* Given a matching address that the identity provider has not verified,
  when the user tries to accept, then it is rejected.
* Given an anonymous visitor, when he opens a valid link, then he sees only
  the request to sign in, without title.
* Given an expired, revoked, used or unknown token, when it is opened, then
  the responses are identical.

### Lifecycle

* Given a new invitation, when created, then it is CREATED and, after
  handover of the mail, PENDING.
* Given a PENDING invitation, when 10 days have passed, then it is
  EXPIRED and cannot be accepted.
* Given an invitation in a final state, when any action is attempted, then
  the state does not change.
* Given a PENDING invitation, when the owner looks for a revoke function,
  then there is none.

### Visibility changes

* Given a wishlist without editors and with PENDING invitations, when the
  owner sets it to PRIVATE, then all these invitations are REVOKED.
* Given a wishlist with editors, when the owner sets it to PRIVATE, then
  this is rejected (existing behavior) and no invitation is revoked.
* Given a PENDING invitation for a USER wishlist, when the owner sets it
  to PUBLIC, then the invitation remains PENDING and can be accepted.
* Given a PENDING invitation for a PUBLIC wishlist, when the owner sets it
  to USER, then the invitation remains PENDING and can be accepted.
* Given a PENDING invitation, when the wishlist becomes PRIVATE during the
  acceptance, then the acceptance fails with an error and neither favorite
  nor editor is created.
* Given a PENDING invitation of variant EDITOR that nevertheless reaches
  acceptance for a PRIVATE wishlist, when the recipient accepts, then he
  gets an error and cannot become editor.

### Accepting and declining

* Given a registered recipient with a PENDING invitation, when he
  accepts, then the wishlist is in his favorites and the invitation is
  ACCEPTED.
* Given a variant NOTIFY invitation, when the recipient accepts, then he
  is not an editor.
* Given a variant EDITOR invitation, when the recipient opens the link and
  only accepts the notification, then he is not an editor.
* Given a variant EDITOR invitation, when the recipient explicitly
  consents, then he is an editor and the wishlist is in his favorites.
* Given a PENDING invitation, when the recipient declines, then it is
  DECLINED and no favorite and no editor relation is created.
* Given an accepted or declined invitation, when the owner looks at the
  wishlist, then he does not see how the recipient reacted.

### Access mode

* Given access mode PUBLIC and an unregistered recipient, when he opens
  the link, then he can register and accept afterwards.
* Given access mode EXISTING with the switch on, when an unregistered
  recipient registers with the matching verified address, then
  registration succeeds and he can accept.
* Given access mode EXISTING with the switch on, when an unregistered
  person registers with a different address through the link, then
  registration is rejected.
* Given access mode EXISTING with the switch off, when an unregistered
  recipient opens the link, then registration is not possible.
* Given access mode EXISTING, when a registered recipient opens the link,
  then he can sign in and accept.
* Given access mode NOBODY, when a recipient opens the link, then he
  cannot sign in or accept, and the invitation remains PENDING.
* Given access mode NOBODY with open invitations, when the mode changes,
  then the invitations are not revoked and expire after 10 days.
* Given an unregistered recipient with variant EDITOR, when he registers,
  then he is not yet editor and must consent afterwards.

## Out of Scope

* Invitations to the application without reference to a wishlist.
* Invitations to PRIVATE wishlists.
* ACLs or finer permissions than owner/editor.
* Editor rights, their revocation and the PRIVATE rule for wishlists with
  editors (already implemented).
* Manual revocation of invitations by the owner.
* Status display of invitations for the owner.
* Mass import of addresses.
* Handling of bounces and delivery errors.
* Alias normalization of e-mail addresses.
* Deleting accounts and changing the owner of a wishlist.

## Related

* ADR: [1. Record architecture decisions](adr-0001-record-architecture-decisions.md)
* Requirements: [1. Record requirements](req-0001-record-requirements.md)

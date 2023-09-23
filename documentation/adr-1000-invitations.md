# 1000. Invitations

Date: 2023-05-13

## Status

Proposed

## Context

On various occasions it is useful for a user to be able to send an invitation to participate to one or more other persons. Reasons for this can be to make someone aware of a wish list in the first place or to invite a person to contribute to a wish list.

## Decision

A general **model** of an invitation can be extended for concrete occasions to the respective special type of invitation. 

A concrete **model** handles offering and accepting of invitations to participte on a specific wishlist.

A **service** offers functionalities to create, delete, send and accept invitations.

A **view** allows handling the accepting of an invitation by a user.

### Models

The abstract base class `Invitation` for the general model holds the following fields:
* `code` -- a randomly generated string that is unique to a particular invitation which is sent with the invitation and must be presented by the invitee to accept the invitation.
* `created_at` -- the time at which the invitation was created.
* `sent` -- a flag indicating whether the invitation has been sent.
* `send_at` -- the time at which the invitation was sent.
* `accepted` -- a flag indicating whether the invitation has been accepted.
* `accepted_at` -- the time at which the invitation was accepted.
* `inviter` -- the user who issued the invitation. 

Other then that the abstract base class requires all specialized invitation types to implement:

* `expired` -- a property that indicates whether the invitation has expired after it has been sent.
* `was_accepted` -- a function that performs the necessary actions for the specific invitation type after it was accepted.

A mixin `ExpiresAfterFixedTime` implements a rule for the property `expired`, according to which an invitation expires after a fixed time specified in the settings.

Processing an invitation is done by calling the appropriate functions of the `InvitationService`.

### Creating and Accepting

A specific invitation is created by calling the corresponding create function of the `InvitationService` and its status is initialised to `sent == False` and `accepted == False`. 

An invitation can be accepted by calling the function `accept_invitation` of the `InnvitationService`. In this case, the caller is fully responsible for ensuring that all conditions for accepting the invitation are met. In particular, that the invitee is actually authorised to accept the invitation.

After an invitation has been accepted, the function `was_accepted` is called for the specific invitation.

### Sending and Receiving

Creating and sending an invitation is a two-step process. This also allows a previously created invitation to be sent later. To send an invitation the function `send_invitation` of the `InnvitationService` is used which changes its status to `sent == True`.  

### WishlistInvitation

To allow users to send an invitation to make someone aware of a wish list, the class `WishlistInvitation` implements the abstract `EmailInvitation` and extends it with a reference to the wish list to which the invitation should apply.

Invitations to wish lists cannot be sent for private wish lists.





After accepting an wishlist invitation an already registered user has direct access. Users who are not yet registered for the project can register first and will then be taken to the wish list.

The invitation link also contains the invitation code so that the invitation is automatically marked as accepted after the first call of the wish list.

## Consequences

A wish list can only be made private again if all previously accepted and all pending invitation are deleted.

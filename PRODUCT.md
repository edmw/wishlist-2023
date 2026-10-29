# Wishlist

## Overview

A web application for managing wish lists: users create lists of wishes, share them with collaborators, reserve and receive wishes, and favorite other people's lists to get notified about new items. Server-rendered Django app in English and German; a rewrite of the 2019 Swift-based Wishlist application.

## Target user

- **Primary user:** A person who wants to collect gift wishes for an occasion (e.g., a birthday) and share them with friends or family
- **Trigger:** An upcoming occasion where others want to give a gift without asking directly
- **Not for:** Businesses or teams managing large-scale product wishlists; this serves personal gift-giving contexts

## User stories

- **Story 1:** When I am planning gifts for someone, I want to create a wishlist and control who can see it, so I can share what I would like without asking directly.
- **Story 2:** When someone shares their list with me, I want to reserve a wish before buying it, so nobody else buys the same thing.
- **Story 3:** When we plan gifts together, I want to collaborate on one list as an editor, so wishes are added and maintained by everyone involved.
- **Story 4:** When I am interested in another person's list, I want to favorite it and get notified about new items, so I can keep up without checking manually.

## Scope

- Accounts: register and log in via email or Open ID Connect; edit profile; configure email and/or Pushover notifications with a test send
- Wishlists: create, edit and delete lists with visibility (private/registered users/public), item ordering, fulfilled/total counter and YAML import and export
- Wishes: add, edit and delete wishes with name, description using Markdown, optional reference link or photo, processed image, and five-level preference; reorder and archive/restore
- Reservations: users reserve a wish (at most one per wish) and can cancel it again; the owner marks a wish as received; optionally mask reservation status until received
- Collaboration: owners add and remove editors; editors perform all wish-level actions but cannot delete the list or change its settings
- Favorites & Notifications: favorite visible lists, toggle the new-wish notification per favorite, delivered asynchronously via email and/or Pushover

## Requirements

| Key | Requirement | Acceptance | Priority | Kind | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Users can register and log in via email or Open ID Connect, and log out again | A new user signs up, logs in from a second browser profile, and sees their personal index | Must | Functional | Partial (no local login)|
| REQ-002 | Owners can create, edit and delete wishlists; deletion requires confirmation with warnings about existing wishes and editors | Create a list, rename it, then start deleting it and verify the warning block lists both risks before confirming | Must | Functional | Complete |
| REQ-003 | Wishlist visibility is private (owner only), registered users, or public; public lists are viewable without login | Set each visibility level in turn and open the list URL in an anonymous browser session | Must | Functional | Partial (no public visibility) |
| REQ-004 | Wishes carry a name, description using Markdown, optional reference link or photo, image, and a five-level preference | Create a wish with all fields set, verify Markdown rendering and that the referenced image is downloaded and processed asynchronously | Must | Functional | Complete |
| REQ-005 | Wishes can be archived and restored; archived wishes cannot be reserved | Archive a wish, attempt to reserve it (blocked), then restore it | Should | Functional | Complete |
| REQ-006 | Logged-in users can reserve a wish (at most one reservation per wish) and cancel the reservation again | Reserve a wish as user A, verify user B is blocked with an error message, then cancel and re-reserve | Must | Functional | Complete |
| REQ-007 | Anonymous users can reserve a wish (at most one reservation per wish) and cancel the reservation again | Reserve a wish as user in an anonymous browser session and cancel the reservation | Should | Functional | Not Implemented |
| REQ-008 | A wish can be marked as received; to unmark a wish its reservation must be released | Mark a reserved wish as received and release its reservation to unmark it | Must | Functional | Complete |
| REQ-009 | Reservation status can optionally be masked per wishlist until a wish becomes received | Enable masking, reserve a wish, and verify owners see an unknown status until the wish is marked received | Should | Functional | Complete |
| REQ-010 | Owners can add and remove editors; editors perform all wish-level actions but cannot delete the list or change its settings | Add an editor by user ID or email, log in as them, edit wishes, and verify list deletion and settings are unavailable to them | Must | Functional | Partial (no UI to add editors) |
| REQ-011 | Private wishlists cannot have collaborators; switching a list to private is rejected while memberships exist | Try adding an editor to a private list (blocked) and try downgrading visibility of a list with editors present (rejected) | Must | Functional | Complete |
| REQ-012 | Users can favorite visible lists and toggle the new-wish notification per favorite | Favorite a list, have its owner add a wish, verify the favoriting user is notified; switch the toggle off and repeat | Should | Functional | Complete |
| REQ-013 | Users can remove favorited lists | Favorite a list, enable notifications and unfavorite list. Verify no more notifications are sent | Should | Functional | Complete |
| REQ-014 | Notifications for new wishes and reservation create or delete are sent asynchronously via email and/or Pushover according to each user's settings | Trigger each event with both channels enabled and disabled in turn and inspect the delivered messages | Must | Functional | Complete |
| REQ-015 | Wishlists can be exported as a YAML file | Open the export action for a list and verify the downloaded file contains its wishes | Could | Functional | Complete |
| REQ-016 | Wishlists can be imported from a YAML file | Open the import action for a list and verify the uploaded file yields a new list | Could | Functional | Not Implemented |
| REQ-017 | The interface is available in English and German | Switch language and verify pages, messages and notifications render in the selected language | Should | Functional | Complete |
| REQ-018 | The application supports three access modes: public (available to everyone, including anonymous visitors), existing (only registered users), and nobody (a maintenance/emergency mode that denies access to all users) | Set each access mode in turn and verify that public allows anonymous access, existing blocks anonymous users while letting registered ones through, and nobody rejects every request regardless of authentication | Must | Functional | Complete |
| REQ-C01 | Strict content security policy with nonces; no inline scripts or styles | Load any page and verify CSP headers reject inline constructs | Must | Constraint | Complete |
| REQ-C02 | The application runs via Docker Compose stacks with PostgreSQL, Redis and Celery and S3-compatible object storage | Start the local stack and verify all services come up and the app is served at 127.0.0.1:13131 | Must | Constraint | Complete |

## Open questions


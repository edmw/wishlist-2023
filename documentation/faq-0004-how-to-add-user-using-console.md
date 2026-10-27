# 4. How to add a user using the console?

Date: 2026-10-26

## Using the `create_user` command (recommended)

Run the management command with the email address of the new user:

```bash
python manage.py create_user user@example.com
```

This creates the user without a usable password (social login only), derives
a username from the local part of the email address, and registers the email
address as verified and primary. The command fails if the email address is
already in use.

To set an explicit username instead of deriving it:

```bash
python manage.py create_user user@example.com --username johndoe42
```

The name must be valid, not reserved, and not already taken — otherwise the
command fails without creating anything.

To link a Google account to the user, pass its Google user ID:

```bash
python manage.py create_user user@example.com --google-id 123456789012345678901
```

This additionally creates a Google social account for the user. The command
fails if the Google ID is already linked to another user.

To skip registering the email address as verified:

```bash
python manage.py create_user user@example.com --skip-email-verification
```

## Manual workflow (fallback)

Open a Django shell (`python manage.py shell`) and run the following steps:

**Step 1: Create the user (without a password)**

Note that `username` is a required field. Derive it from the local part of
the email address and make sure it does not collide with an existing username:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user(username="user", email="user@example.com", password=None)
```

**Step 2: Verify the email address** *(optional, but usually recommended)*

```python
from allauth.account.models import EmailAddress

EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
```

**Step 3: Create a Google social account**

```python
from allauth.socialaccount.models import SocialAccount

social_account = SocialAccount.objects.create(
    user=user,
    provider="google",
    uid="123456789012345678901",  # Google user ID
    extra_data={
        "id": "123456789012345678901",
        "email": "user@example.com",
        "verified_email": True,
    },
)

print(f"User {user.email} created with Google social account!")
```

**How to find the Google UID of an existing user**

Start the application locally and set `access` to `PUBLIC` in `core/apps.py`. Sign in with the target Google account, then look up the user in the database and read their UID:

```python
SocialAccount.objects.get(pk=X).uid
```

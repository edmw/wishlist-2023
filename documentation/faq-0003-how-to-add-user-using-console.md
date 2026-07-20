# 3. How to add a user using the console?

Date: 2024-01-01

Open a Django shell (`python manage.py shell`) and run the following steps:

**Step 1: Create the user (without a password)**

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user(email="user@example.com", password=None)
```

**Step 2: Verify the email address** *(optional, but usually recommended)*

```python
from allauth.account.models import EmailAddress

EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
```

**Step 3: Create a Google social account**

```python
from allauth.socialaccount.models import SocialAccount, SocialApp

google_app = SocialApp.objects.get(provider="google")

social_account = SocialAccount.objects.create(
    user=user,
    provider="google",
    uid="123456789012345678901",  # Google user ID
    extra_data={
        "name": "Example User",
        "email": "user@example.com",
        "picture": "https://example.com/avatar.jpg",
    },
)

print(f"User {user.email} created with Google social account!")
```

**How to find the Google UID of an existing user**

Start the application locally and set `access` to `PUBLIC` in `core/apps.py`. Sign in with the target Google account, then look up the user in the database and read their UID:

```python
SocialAccount.objects.get(pk=X).uid
```

# 2. How to configure sensitive data?

Date: 2023-03-01
Updated: 2026-07-29

Application configuration is stored in the files of the respective environment directory, for example `environments/local`.

Some configuration values, such as identifiers or passwords, may not be stored in this central location. Therefore, sensitive values can be stored in a mirrored copy of the non-sensitive configuration files.

In a directory named `private`, create a mirrored copy of the `local` environment:

```
private/environments/local/docker-compose.env.yml
private/environments/local/webapp.env
private/environments/local/secrets/webapp.env
```

Use `docker-compose.env.yml` to overwrite the environment for the relevant docker containers:

```
---
services:
  app:
    env_file:
      - private/environments/local/webapp.env
      - private/environments/local/secrets/webapp.env
  worker:
    env_file:
      - private/environments/local/webapp.env
      - private/environments/local/secrets/webapp.env
  beat:
    env_file:
      - private/environments/local/webapp.env
      - private/environments/local/secrets/webapp.env
```

*Note: Any value from a non-critical configuration file that is not overwritten in a private configuration file is also passed to the environment.*

You can now add sensitive information, such as identifiers, into `private/environments/local/webapp.env`:

```
AUTH_GOOGLE_CLIENT_ID="the_real_google_identifier"
...
```

Or passwords, to `private/environments/local/secrets/webapp.env`:

```
AUTH_GOOGLE_SECRET="the_real_google_secret"
...
```

Any `inv` task that launches a docker container with the corresponding environment will now automatically include the private values.

## Encrypted Secrets with WEBAPP_KEY

Some sensitive configuration values in this application are encrypted using the **WEBAPP_KEY**, a Fernet-based symmetric encryption key. This provides an additional layer of security for secrets that are stored in environment files.

### Which Values Are Encrypted?

The following environment variables are decrypted at runtime using the WEBAPP_KEY:

| Variable | Purpose | Location |
|----------|---------|----------|
| `DATABASE_PASSWORD` | Database password | `secrets/webapp.env` |
| `STORAGE_SECRET_KEY` | Object Storage secret access key | `secrets/webapp.env` |
| `EMAIL_SMTP_PASSWORD` | Email SMTP server password | `secrets/webapp.env` |
| `PUSHOVER_APPLICATION_TOKEN` | Pushover notification service API token | `secrets/webapp.env` |
| `AUTH_GOOGLE_SECRET` | Google OAuth client secret | `secrets/webapp.env` |

### How It Works

1. **WEBAPP_KEY Management**: The `WEBAPP_KEY` is stored **securely in the system keyring** (not in files):
   - **Local/Staging/Production**: Retrieved from the system keyring via `keyring.get_password("wishlist-webapp_key", <environment>)`
   - **Testing only**: Can use a hardcoded key in `environments/testing/webapp.env` for CI/CD purposes
   - The `docker_runner.py` automatically fetches the key from the keyring and passes it as `WEBAPP_KEY` environment variable to Docker containers

2. **Encryption & Decryption**: At startup, the application:
   - Reads the `WEBAPP_KEY` from the environment and creates a `Fernet` cipher object
   - Reads encrypted values from environment files (stored in `secrets/webapp.env`)
   - Automatically decrypts them using: `Fernet.decrypt(encrypted_value.encode("ascii")).decode("ascii")`

### How to Encrypt Secrets

To encrypt a secret value, use Python's `cryptography` library:

```python
from cryptography.fernet import Fernet

# Use your WEBAPP_KEY (base64-encoded)
master_key = "S5OA3a2sChQqZF3BIW2wSlgTjr0KwdQqXkTNJcc1YIs="
secret_value = "my_actual_secret_password"

# Encrypt
encrypted = Fernet(master_key).encrypt(secret_value.encode("ascii")).decode("ascii")
print(encrypted)
# Output: gAAAAABj3ZUiNkA8ad9yuYWcVnJcbA1_g51lUT0ErOTRdb4OkpUSHSrLTegVmXWKz5dvNQMHTgFYrS3fTNUql1wTspfhMCvld1jMBZGz0c1_Cv3sGt-qCDw=
```

### Configuration Steps

1. **Generate or obtain a WEBAPP_KEY**:
   ```python
   from cryptography.fernet import Fernet
   key = Fernet.generate_key().decode("ascii")
   print(key)  # Save this in your system keyring
   ```

2. **Store WEBAPP_KEY in system keyring** (recommended for local/staging/production):
   ```bash
   # macOS (Keychain)
   security add-generic-password -a "local" -s "wishlist-webapp_key" -w "your_key_here"
   security add-generic-password -a "local-deploy" -s "wishlist-webapp_key" -w "your_key_here"
   
   # Linux (Secret Service via keyring CLI)
   keyring set wishlist-webapp_key local
   keyring set wishlist-webapp_key local-deploy
   
   # Windows (Credential Manager via keyring CLI)
   keyring set wishlist-webapp_key local
   keyring set wishlist-webapp_key local-deploy
   ```
   ⚠️ **Use different keys for local and local-deploy!**

3. **For Testing Only**: A hardcoded key can be placed in `environments/testing/webapp.env`:
   ```
   WEBAPP_KEY="S5OA3a2sChQqZF3BIW2wSlgTjr0KwdQqXkTNJcc1YIs="
   ```
   ⚠️ **Never commit real secrets to version control!**

4. **Create the secrets file structure**:
   ```
   environments/local/secrets/webapp.env
   private/environments/local/secrets/webapp.env (optional override)

   environments/local-deploy/secrets/webapp.env
   private/environments/local-deploy/secrets/webapp.env (optional override)
   ```

5. **Encrypt each secret and add to secrets/webapp.env**:
   ```bash
   # For each secret value, use the encryption method above
   AUTH_GOOGLE_SECRET="encrypted_value_here"
   STORAGE_SECRET_KEY="encrypted_value_here"
   PUSHOVER_APPLICATION_TOKEN="encrypted_value_here"
   DATABASE_PASSWORD="encrypted_value_here"
   EMAIL_SMTP_PASSWORD="encrypted_value_here"
   ```

6. **Update docker-compose.env.yml** (if using Docker):
   ```yaml
   ---
   services:
     app:
       env_file:
         - environments/local/webapp.env
         - environments/local/secrets/webapp.env
     worker:
       env_file:
         - environments/local/webapp.env
         - environments/local/secrets/webapp.env
     beat:
       env_file:
         - environments/local/webapp.env
         - environments/local/secrets/webapp.env
   ```
   
   *Note: The `WEBAPP_KEY` itself is not stored in env files for local/staging/production—it's injected by the task runner from the system keyring.*

### Important Notes

- **WEBAPP_KEY is NOT stored in files** (except for testing)

  The key is managed securely via the system keyring and dynamically injected into Docker containers by `docker_runner.py`.

  Only use hardcoded key in `environments/testing/webapp.env` for testing. For local/staging/production, always use the system keyring.

- **Decryption only works if WEBAPP_KEY is set**

  If `WEBAPP_KEY` is missing or invalid from the keyring, the application will fail to read encrypted values.

- **Encryption is per-key**

  Each `WEBAPP_KEY` can only decrypt values encrypted with that specific key.

- **Base64 encoding**

  Keys and encrypted values are base64-encoded for safe storage in text files.

- **Non-encrypted override**

  Plain (unencrypted) values provided via environment variables still work — encrypted values are optional. If an encrypted value is not provided, the default value is used instead.

  

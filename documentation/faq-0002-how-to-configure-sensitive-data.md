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
  
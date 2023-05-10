# 2. How to do sensitive configuration?

Date: 2023-03-01

Configuration of the application is recorded in the files of the respective environment directory, for example `environments/local`.

Some configuration values may not be stored in this central location, such as identifiers or passwords. Therefore, sensitive values can be stored in a mirror of the non-critical configuration files. This mirror must be created as follows:

In a directory named `private` create for a mirror of the `local` environment:

```
private/environments/local/docker-compose.env.yml
private/environments/local/webapp.env
private/environments/local/secrets/webapp.env
```

Use `docker-compose.env.yml` to overwrite the environment for the desired docker containers:

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

*Note: Any value from a non-critical configuration file that is not overwritten in a private configuration file is also transferred to the environment.*

Now you can place sensitive information, for example identifiers, into `private/environments/local/webapp.env` like so:

```
AUTH_GOOGLE_CLIENT_ID="the_real_google_identifier"
...
```

Or passwords, into `private/environments/local/secrets/webapp.env` like so:

```
AUTH_GOOGLE_SECRET="the_real_google_secret"
...
```

Any `make` target that launches docker container with the corresponding environment will now automatically include the private values.

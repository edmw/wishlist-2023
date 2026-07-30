# Wishlist

Wishlist is a web application written in Python with the Django framework for managing wish lists. It allows users to create lists of items they want most and share them with others.

This is a rewrite of the [2019 Wishlist web application written in Swift](https://github.com/edmw/wishlist).

## Development Environment

The application is built and run using Docker containers for development.

### Setup Environment on Host

The following instructions create a virtual environment for the project using Python 3.12, install `invoke` with dependencies into that environment, and, finally, perform all necessary steps to obtain a working development environment (pyenv must be available).

```
$ cd <PROJECT_DIRECTORY>
$ pyenv install 3.12
$ pyenv virtualenv 3.12 wishlist-12
$ pyenv local wishlist-12
$ pyenv shell wishlist-12
$ python -m pip install --upgrade pip
$ python -m pip install invoke semver keyring rich pyyaml
$ inv make.install-development
```

Alternatively, it is also possible to install `invoke` globally for use in multiple projects using pipx:

```
$ pipx install invoke
$ pipx inject invoke semver keyring rich pyyaml
```

Of course, a separate virtual environment should still be created for the project:

```
$ cd <PROJECT_DIRECTORY>
$ pyenv install 3.12
$ pyenv virtualenv 3.12 wishlist-12
$ pyenv local wishlist-12
$ pyenv shell wishlist-12
$ inv make.install-development
```

## Run Development Server

The Django web server is used to execute the web application for development. The server can be started with Django Debug Mode turned on or off and Debug Adapter Protocol activated or deactivated.

Run with Django Debug Mode turned **on** and Debug Adapter Protocol **activated**:

```
$ inv run
```

Run with Django Debug Mode turned **off** and Debug Adapter Protocol **activated**:

```
$ DJANGO_DEBUG=False inv run
```

Run with Django Debug Mode turned **on** and Debug Adapter Protocol **deactivated**:

```
$ inv run.development
```

Run with Django Debug Mode turned **off** and Debug Adapter Protocol **deactivated**:

```
$ DJANGO_DEBUG=False inv run.development
```

The development image contains several **additional tools and libraries** that enable development tasks and debugging.

## Run Production Version

`Gunicorn` is used to execute the web application.

```
$ inv run.production
```

This uses the deployment image with only **required tools and libraries** installed and Django Debug Mode turned **off**.

## Release a new Version

Release a new version of the project using either

```
inv release.patch
inv release.minor
inv release.major
```

which will bump the version number accordingly, build a new release image, commit a version tag, and push the new image to the registry.

Note: To build a new release, `main` must be the current branch, `main` must be a tracking branch, `main` must be up-to-date, and `main` must not be dirty.

Note: Currently, the history will not be updated. Best practice is to update the history file before running `inv release.*`.

## Test the Application

* `pytest` -- unittest runner
* `coverage` -- code coverage reporter

```
inv test
```

```
inv test.debug
```

```
inv test.coverage
```

## Check the Application

* `ruff` -- static code analyzer
* `bandit` -- security issue linter

```
inv check
```

## Manage the Application

* `inv manage.console`
  * Start a Python console for the web application.
* `inv manage.migrations`
  * Create or update migrations for the web application.
* `inv manage.translations`
  * Create or update translations for the web application.
* `inv manage.dumpdata`
  * Dump the data from the database of the web application to a file.
* `inv manage.shell`
  * Start a shell in a local service container (default: app) after the server has been started.
* `inv manage.connect-database`
  * Connect to the database console of the local service container after the server has been started.
* `inv manage.connect-datastore`
  * Connect to the datastore console of the local service container after the server has been started.

## Make the Environment

* `inv`
  * List and describe all available tasks.
* `inv make.clean`
* `inv make.pin`
* `inv make.pin-development`
* `inv make.pin-production`
* `inv make.update`
* `inv make.update-development`
* `inv make.update-production`
* `inv make.install-development`
* `inv make.install-production`
* `inv make.sync-development`
* `inv make.sync-production`

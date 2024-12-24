# Wishlist

[![Build, Check, Test](https://github.com/edmw/wishlist-2023/actions/workflows/main.yml/badge.svg)](https://github.com/edmw/wishlist-2023/actions/workflows/main.yml)

Wishlist is a web application written in Python with the Django framework for managing wish lists. It allows users to create lists of items they want most and share them with others.

This is a rewrite of the [2019 Wishlist web application written in Swift](https://github.com/edmw/wishlist).

## Development Environment

The application is built and run with Docker containers for development.

### Setup Environment on Host

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

## Make

### Webapp

```
$ make webapp-translations
$ make webapp-migrations
$ make webapp-dumpdata
```

### Testing

```
$ make test
$ make debugtest
$ make test-coverage
$ make test-down
```

### Checking

```
$ make check
$ make check-down
```

### Building

```
$ make build-develop
$ make build-deploy
$ make build-release.patch
$ make build-release.minor
$ make build-release.major
```

### Releasing

```
$ make release.patch
$ make release.minor
$ make release.major
$ make release-push
```

### Dependencies

```
$ make dependencies-install-deployment
$ make dependencies-install-development
$ make dependencies-pin-deployment
$ make dependencies-pin-development
$ make dependencies-pin-all
$ make dependencies-update-deployment
$ make dependencies-update-development
$ make dependencies-update-all
```

### Environment

```
$ make clean

$ make environment-upgrade

$ make shell.%s
$ make shell  # make shell.app
$ make console
$ make connect-database
$ make connect-datastore
$ make run-shell.%
$ make run-shell  # make run-shell.app
$ make run-console
```

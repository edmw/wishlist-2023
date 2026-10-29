# HISTORY

## [x.x.x]

* 🖌️ fix sign out button missing its background

## [2.4.0]

* 🛠️ add management command to a create user 
* 🛠️ make dependency update tasks preview-only by default
* 🪛 fix missing page title on account pages
* 🛠️ upgrade python to 3.14
* 🛠️ upgrade django to 6.0
* 🛠️ upgrade project dependencies
* 🛠️ switch to django content security policy middleware
* 🛠️ replace minio with seaweedfs in development
* 🛠️ make checks run in testing environment
* 🪛 fix interactive commands
* 🪛 cleanup code (fix typing errors)

## [2.3.1]

* 🪛 minor fixes
* 🪛 cleanup code (fix typing errors)

## [2.3.0]

* 🖼️ add removal of memberships by wishlist owner
* 🖌️ fix missing translation

## [2.2.0]

* 🖼️ enable viewing memberships for wishlists

## [2.1.0]

* 🛠️ upgrade django to 5.2
* 🛠️ upgrade project dependencies

## [2.0.0]

* 🖼️ add wishlist collaboration; users can be editors for other lists
* 🛠️ add grilling skills from https://www.aihero.dev/grill-with-docs

## [1.9.2]

* 🪛 fix import order which led to missing Celery configuration

## [1.9.1]

* 🪛 fix potential race condition when generating photos

## [1.9.0]

* 🖼️ always show the button to mark a wish as received and display an error
  message if the button is clicked for a wish that cannot be flagged
* 🛠️ switch from Makefile to Invoke
* 🛠️ update Dockerfile to use Node setup script
* 🛠️ improve typing
* 🛠️ improve tooling

## [1.8.2]

* 🪛 fix handling of retries when generating images interactively

## [1.8.1]

* 🪛 fix handling of connection errors when generating images

## [1.8.0]

* 🖼️ display number of actual and number of total wishes for wishlists
* 🛠️ upgrade python to 3.12
* 🛠️ upgrade django to 5.1
* 🛠️ upgrade project dependencies
* 🛠️ switch from django-types to django-stubs

## [1.7.0]

* 🛠️ upgrade node to version 20
* 🛠️ upgrade python dependencies
* 🪛 fix check findings

## [1.6.0]

* 🛠️ upgrade base image to debian bookworm

## [1.5.1]

* 🪛 fix template errors
* 🛠️ improve error handling for wish_image_from_reference_photo command

## [1.5.0]

* 🛠️ add use of base62 encoded ids to management commands

## [1.4.0]

* 🛠️ add management command to generate images for reference photos
* 🛠️ combine make_password and create_password management commands into hash_password

## [1.2.0]

* 🛠️ upgrade project dependencies
* 🛠️ add lenses for querying models
* 🛠️ refactor models
* 🛠️ settings: remove obsolete handling for redis username
* 🛠️ vscode: update launch settings
* 🛠️ makefile: add target for viewing logs
* 🪛 fix page contexts and includes
* 🪛 python: disable optimization
* 🪛 docker compose: fix dependencies

## [1.1.0]

* 🖼️ add markdown for description
* 🛠️ update project dependencies
* 🛠️ add region marker to settings
* 🛠️ enable docker buildkit caching for pip install
* 🪛 CI: disable automatic runs
* 🪛 CI: fix cleanup action
* 🪛 makefile: fix debugtest target
* 🖊️ fix history

## [1.0.0]
🚀

## Legend

🖼️ ... add feature
🖌️ ... fix feature
📚 ... add documentation
🖊️ ... fix documentation
🛠️ ... add machinery
🪛 ... fix machinery

MAKE_PYTHON := python
MAKE_DOCKER := docker
MAKE_DOCKER_COMPOSE := docker compose
MAKE_DOCKER_PYTHON := python -W ignore::DeprecationWarning

MAKE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKE_DIR := $(dir $(MAKE_PATH))

BUILD_PLATFORM ?= linux/arm64
BUILD_IMAGE_NAME := wishlist-webapp

.DEFAULT_GOAL := run


########  ##     ## ##    ## ##    ## #### ##    ##  ######
##     ## ##     ## ###   ## ###   ##  ##  ###   ## ##    ##
##     ## ##     ## ####  ## ####  ##  ##  ####  ## ##
########  ##     ## ## ## ## ## ## ##  ##  ## ## ## ##   ####
##   ##   ##     ## ##  #### ##  ####  ##  ##  #### ##    ##
##    ##  ##     ## ##   ### ##   ###  ##  ##   ### ##    ##
##     ##  #######  ##    ## ##    ## #### ##    ##  ######

# compose project settings for running
RUN_WEBAPP := --project-name wishlist --project-directory .

# compose configuration for running

ifneq ($(wildcard private/environments/local/docker-compose.env.yml),)
    RUN_WEBAPP_LOCAL_ENV := -f private/environments/local/docker-compose.env.yml
else
    RUN_WEBAPP_LOCAL_ENV :=
endif
RUN_WEBAPP_LOCAL := $(RUN_WEBAPP) \
	-f environments/local/docker-compose.yml $(RUN_WEBAPP_LOCAL_ENV) \
	-f environments/common/docker-compose.database.yml \
	-f environments/common/docker-compose.datastore.yml \
	-f environments/common/docker-compose.files.yml

RUN_WEBAPP_LOCAL_KEY := `security find-generic-password -w -s 'wishlist-webapp_key' -a 'local'`
RUN_DOCKER_LOCAL := WEBAPP_KEY=$(RUN_WEBAPP_LOCAL_KEY) \
	$(MAKE_DOCKER_COMPOSE) $(RUN_WEBAPP_LOCAL)

# compose configuration for running deployment version

ifneq ($(wildcard private/environments/local-deploy/docker-compose.env.yml),)
    RUN_WEBAPP_LOCAL_DEPLOY_ENV := -f private/environments/local-deploy/docker-compose.env.yml
else
    RUN_WEBAPP_LOCAL_DEPLOY_ENV :=
endif
RUN_WEBAPP_LOCAL_DEPLOY := $(RUN_WEBAPP) \
	-f environments/local-deploy/docker-compose.yml $(RUN_WEBAPP_LOCAL_DEPLOY_ENV)

RUN_WEBAPP_LOCAL_DEPLOY_KEY := `security find-generic-password -w -s 'wishlist-webapp_key' -a 'local-deploy'`
RUN_DOCKER_LOCAL_DEPLOY := WEBAPP_KEY=$(RUN_WEBAPP_LOCAL_DEPLOY_KEY) \
	$(MAKE_DOCKER_COMPOSE) $(RUN_WEBAPP_LOCAL_DEPLOY)

.PHONY: --run-banner.%
--run-banner.%:
	@ printf "\033[48;5;000m 🚀🚀🚀  " && echo "$(*)\c" | sed -r 's/_/ /g' && echo " \033[0m\n"

.PHONY: run
run: build-develop --run-banner.Running_Local_Server
	echo; $(RUN_DOCKER_LOCAL) -f environments/local/docker-compose.debug.yml up

.PHONY: run-develop
run-develop: build-develop --run-banner.Running_Local_Server_with_Development_Version
	echo; $(RUN_DOCKER_LOCAL) up

.PHONY: logs
logs:
	@ $(RUN_DOCKER_LOCAL) logs -f app worker beat

.PHONY: down
down: build-develop
	@ $(RUN_DOCKER_LOCAL) down

.PHONY: run-deploy
run-deploy: build-deploy --run-banner.Running_Local_Server_with_Production_Version
	echo; $(RUN_DOCKER_LOCAL_DEPLOY) up

.PHONY: down-deploy
down-deploy: build-develop
	@ $(RUN_DOCKER_LOCAL_DEPLOY) down


##      ## ######## ########     ###    ########  ########
##  ##  ## ##       ##     ##   ## ##   ##     ## ##     ##
##  ##  ## ##       ##     ##  ##   ##  ##     ## ##     ##
##  ##  ## ######   ########  ##     ## ########  ########
##  ##  ## ##       ##     ## ######### ##        ##
##  ##  ## ##       ##     ## ##     ## ##        ##
 ###  ###  ######## ########  ##     ## ##        ##

RUN_DOCKER_RUN := run \
	--quiet-pull \
	--rm \
	--entrypoint="" \
	app

.PHONY: --webapp-banner.%
--webapp-banner.%:
	@ printf "\033[48;5;000m 🔩🔩🔩  " && echo "$(*)\c" | sed -r 's/_/ /g' && echo " \033[0m\n"

.PHONY: webapp-translations
webapp-translations: build-develop --webapp-banner.Make_Translations
	@ $(RUN_DOCKER_LOCAL) $(RUN_DOCKER_RUN) \
		$(MAKE_DOCKER_PYTHON) manage.py webapp_make_translations

.PHONY: webapp-migrations
webapp-migrations: build-develop --webapp-banner.Make_Migrations
	@ $(RUN_DOCKER_LOCAL) $(RUN_DOCKER_RUN) \
		$(MAKE_DOCKER_PYTHON) manage.py webapp_make_migrations

.PHONY: webapp-dumpdata
webapp-dumpdata: build-develop --webapp-banner.Dump_Data
	@ $(RUN_DOCKER_LOCAL) $(RUN_DOCKER_RUN) \
		$(MAKE_DOCKER_PYTHON) manage.py dumpdata \
			core socialaccount account auth \
			--natural-foreign \
			--format=yaml > core_`date +%d-%m-%Y"_"%H_%M_%S`.dump.yaml


######## ########  ######  ######## #### ##    ##  ######
   ##    ##       ##    ##    ##     ##  ###   ## ##    ##
   ##    ##       ##          ##     ##  ####  ## ##
   ##    ######    ######     ##     ##  ## ## ## ##   ####
   ##    ##             ##    ##     ##  ##  #### ##    ##
   ##    ##       ##    ##    ##     ##  ##   ### ##    ##
   ##    ########  ######     ##    #### ##    ##  ######

TEST_WEBAPP := --project-name wishlist-test --project-directory .

TEST_WEBAPP_TESTING := $(TEST_WEBAPP) \
	-f environments/testing/docker-compose.yml \
	-f environments/common/docker-compose.database.yml \
	-f environments/common/docker-compose.datastore.yml

TEST_DOCKER := $(MAKE_DOCKER_COMPOSE) $(TEST_WEBAPP_TESTING)
TEST_DOCKER_DEBUG := $(TEST_DOCKER) \
	-f environments/testing/docker-compose.debug.yml

TEST_DOCKER_RUN := run \
	--quiet-pull \
	--service-ports \
	--rm \
	app
TEST_DOCKER_RUN_TEST := $(TEST_DOCKER_RUN) \
	$(MAKE_DOCKER_PYTHON) -Xfrozen_modules=off manage.py webapp_test

.PHONY: --test-banner.%
--test-banner.%:
	@ printf "\033[48;5;000m 🚀🚀🚀  " && echo "$(*)\c" | sed -r 's/_/ /g' && echo " \033[0m\n"

.PHONY: test-ci
test-ci: --test-banner.Testing_Local_Server
	echo; $(TEST_DOCKER) $(TEST_DOCKER_RUN_TEST) $(TEST_SPEC); exit_code=$$?; make test-down; exit $$exit_code

.PHONY: test
test: build-develop test-ci ;

.PHONY: debugtest
debugtest: build-develop --test-banner.Testing_Local_Server
	echo; $(TEST_DOCKER_DEBUG) $(TEST_DOCKER_RUN_TEST) --debug $(TEST_SPEC); exit_code=$$?; make test-down; exit $$exit_code

.PHONY: test-coverage-ci
test-coverage-ci: --test-banner.Testing_Server_with_Coverage
	echo; $(TEST_DOCKER) $(TEST_DOCKER_RUN_TEST) --coverage $(TEST_SPEC); exit_code=$$?; make test-down; exit $$exit_code

.PHONY: test-coverage
test-coverage: build-develop test-coverage-ci ;

.PHONY: test-down
test-down:
	@ $(TEST_DOCKER) down


 ######  ##     ## ########  ######  ##    ## #### ##    ##  ######
##    ## ##     ## ##       ##    ## ##   ##   ##  ###   ## ##    ##
##       ##     ## ##       ##       ##  ##    ##  ####  ## ##
##       ######### ######   ##       #####     ##  ## ## ## ##   ####
##       ##     ## ##       ##       ##  ##    ##  ##  #### ##    ##
##    ## ##     ## ##       ##    ## ##   ##   ##  ##   ### ##    ##
 ######  ##     ## ########  ######  ##    ## #### ##    ##  ######

TEST_DOCKER_RUN_CHECK := $(TEST_DOCKER_RUN) \
	$(MAKE_DOCKER_PYTHON) manage.py webapp_check

.PHONY: --check-banner.%
--check-banner.%:
	@ printf "\033[48;5;000m 🕵️‍♀️🕵️‍♀️🕵️‍♀️  " && echo "$(*)\c" | sed -r 's/_/ /g' && echo " \033[0m\n"

.PHONY: check-ci
check-ci: --check-banner.Checking_Code
	echo; $(TEST_DOCKER) $(TEST_DOCKER_RUN_CHECK); exit_code=$$?; make check-down; exit $$exit_code

.PHONY: check
check: build-develop check-ci ;

.PHONY: check-down
check-down:
	@ $(TEST_DOCKER) down


########  ##     ## #### ##       ########  #### ##    ##  ######
##     ## ##     ##  ##  ##       ##     ##  ##  ###   ## ##    ##
##     ## ##     ##  ##  ##       ##     ##  ##  ####  ## ##
########  ##     ##  ##  ##       ##     ##  ##  ## ## ## ##   ####
##     ## ##     ##  ##  ##       ##     ##  ##  ##  #### ##    ##
##     ## ##     ##  ##  ##       ##     ##  ##  ##   ### ##    ##
########   #######  #### ######## ########  #### ##    ##  ######

.PHONY: build-develop
build-develop:
	@ BUILD_BASE_IMAGE=$(shell $(MAKE_PYTHON) development/make.py get_build_base_image); $(MAKE_PYTHON) development/make_build.py --platform "$(BUILD_PLATFORM)" --base "$$BUILD_BASE_IMAGE" --name "$(BUILD_IMAGE_NAME)" develop

.PHONY: build-deploy
build-deploy:
	@ BUILD_BASE_IMAGE=$(shell $(MAKE_PYTHON) development/make.py get_build_base_image); $(MAKE_PYTHON) development/make_build.py --platform "$(BUILD_PLATFORM)" --base "$$BUILD_BASE_IMAGE" --name "$(BUILD_IMAGE_NAME)" deploy

--guard-build-release.%:
	@ if [ ! "$*" = "patch" -a ! "$*" = "minor" -a ! "$*" = "major" ]; then \
		echo "build-release: bump must be either one of 'patch', 'minor', 'major' - not '$*'"; \
		exit 1; \
	fi

.PHONY: build-release.%
build-release.%: --guard-build-release.%
	@ BUILD_BASE_IMAGE=$(shell $(MAKE_PYTHON) development/make.py get_build_base_image); $(MAKE_PYTHON) development/make_build.py --base "$$BUILD_BASE_IMAGE" --name "$(BUILD_IMAGE_NAME)" release --bump="$*"


########  ######## ##       ########    ###     ######  #### ##    ##  ######
##     ## ##       ##       ##         ## ##   ##    ##  ##  ###   ## ##    ##
##     ## ##       ##       ##        ##   ##  ##        ##  ####  ## ##
########  ######   ##       ######   ##     ##  ######   ##  ## ## ## ##   ####
##   ##   ##       ##       ##       #########       ##  ##  ##  #### ##    ##
##    ##  ##       ##       ##       ##     ## ##    ##  ##  ##   ### ##    ##
##     ## ######## ######## ######## ##     ##  ######  #### ##    ##  ######

--guard-release.%:
	@ if [ ! "$*" = "patch" -a ! "$*" = "minor" -a ! "$*" = "major" ]; then \
		echo "release: bump must be either one of 'patch', 'minor', 'major' - not '$*'"; \
		exit 1; \
	fi

.PHONY: release.%
release.%: --guard-release.% check build-release.%
	@ $(MAKE_PYTHON) development/make_release.py --name "$(BUILD_IMAGE_NAME)" push


######## ##    ## ##     ## #### ########   #######  ##    ## ##     ## ######## ##    ## ########
##       ###   ## ##     ##  ##  ##     ## ##     ## ###   ## ###   ### ##       ###   ##    ##
##       ####  ## ##     ##  ##  ##     ## ##     ## ####  ## #### #### ##       ####  ##    ##
######   ## ## ## ##     ##  ##  ########  ##     ## ## ## ## ## ### ## ######   ## ## ##    ##
##       ##  ####  ##   ##   ##  ##   ##   ##     ## ##  #### ##     ## ##       ##  ####    ##
##       ##   ###   ## ##    ##  ##    ##  ##     ## ##   ### ##     ## ##       ##   ###    ##
######## ##    ##    ###    #### ##     ##  #######  ##    ## ##     ## ######## ##    ##    ##

.PHONY: environment-upgrade
environment-upgrade:
	pip --require-virtualenv --quiet install --upgrade pip pip-tools wheel

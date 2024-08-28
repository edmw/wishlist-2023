# Base
# This is the base for either the development image or the deployment image.
# The development image will be build *upon* the contents this image,
# while the deployment image will be build *with* the contents of this image.
#
# Contains
# - Python runtime
# - Javascript/Node runtime
FROM python:3.11-slim-bookworm AS docker-base
RUN apt-get update -y && apt-get install -y curl gpg gettext
# Install Node and Node Package Manager.
RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key \
    | gpg --dearmor \
    | tee /usr/share/keyrings/nodesource.gpg \
    >/dev/null
RUN echo 'deb [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_19.x bookworm main' > /etc/apt/sources.list.d/nodesource.list && \
    echo 'deb-src [signed-by=/usr/share/keyrings/nodesource.gpg] https://deb.nodesource.com/node_19.x bookworm main' >> /etc/apt/sources.list.d/nodesource.list
RUN apt-get update -y && apt-get install -y nodejs


# Builder
# This is the builder for either the development image or the deployment image.
# The development image will be build *upon* the contents this builder,
# while the deployment image will be build *with* the contents of this builder.
#
# Contains
# - all of base image
# - built Frontend resources
FROM docker-base AS docker-builder
# Setup Web Application build environment.
ENV BUILD_HOME=/build
WORKDIR $BUILD_HOME
# Build Frontend resources for development.
COPY webapp-frontend/package.json webapp-frontend/package-lock.json ./
RUN npm run build


# Development Installer
# This installer is for the development image *only*.
# Installs all dependencies for running the server and development.
# - installed Python Packages
FROM docker-builder as develop-installer
# Setup Web Application install environment.
ENV INSTALL_HOME=/
WORKDIR $INSTALL_HOME
# Install Python dependencies for development.
COPY requirements-development.txt ./
RUN --mount=type=cache,target=/root/.cache \
    python -m pip install --upgrade pip \
    && python -m pip install --upgrade -r requirements-development.txt


# Development Image
# This is the image for development. Contains all the resources and dependencies
# for running, building and developing the webapp. The webapp’s code need to be
# mounted into this image.
FROM develop-installer as develop
# Setup Web Application environment.
ENV APP_HOME=/webapp
ENV APP_STATIC=/webapp-static
ENV APP_USER=webapp
# Add user for running the server.
RUN mkdir -p "/home/$APP_USER" && \
    groupadd -r $APP_USER && \
    useradd -r \
    -g $APP_USER --groups staff \
    -d /home/$APP_USER \
    -s /sbin/nologin \
    $APP_USER
# Create directories for the server.
RUN mkdir -p "$APP_HOME" && \
    mkdir -p "$APP_STATIC" && \
    chown -R $APP_USER:$APP_USER $APP_HOME && \
    chown -R $APP_USER:$APP_USER $APP_STATIC
# Python: Optimization.
ENV PYTHONOPTIMIZE=
# Python: Warning control.
ENV PYTHONWARNINGS=always
# Python: Force the stdout and stderr streams to be unbuffered.
ENV PYTHONUNBUFFERED=1
# Python: Disallow creation of byte-code files.
ENV PYTHONDONTWRITEBYTECODE=1
#
WORKDIR $APP_HOME
USER $APP_USER


# Production Installer
# This installer is for the deployment image *only*.
# Installs all dependencies for running the server in production.
# - installed Python Packages (without development dependencies)
FROM python:3.11-slim-bookworm as deploy-installer
# Setup Web Application install environment.
ENV INSTALL_HOME=/
WORKDIR $INSTALL_HOME
# Install Frontend resources for production.
COPY --from=docker-builder /build/dist /build/dist
# Install Python dependencies for production.
COPY requirements.txt .
RUN python -m pip install --upgrade pip && python -m pip install --upgrade -r requirements.txt


# Deployment Image
# This is the image for deployment. Contains all the resources and dependencies
# for running the webapp in production. The webapp’s code is copied into this
# image.
FROM deploy-installer as deploy
LABEL org.opencontainers.image.description="Web application for managing wish lists."
# Setup Web Application environment.
ENV APP_HOME=/webapp
ENV APP_STATIC=/webapp-static
ENV APP_USER=webapp
# Add user for running the server.
RUN mkdir -p "/home/$APP_USER" && \
    groupadd -r $APP_USER && \
    useradd -r \
    -g $APP_USER --groups staff \
    -d /home/$APP_USER \
    -s /sbin/nologin \
    $APP_USER
# Create directories for the server.
RUN mkdir -p "$APP_HOME" && \
    mkdir -p "$APP_STATIC" && \
    chown -R $APP_USER:$APP_USER $APP_HOME && \
    chown -R $APP_USER:$APP_USER $APP_STATIC
# Python: Optimization.
# 03/24 Optimization must be disabled because pycparser will break if
# docstrings are removed by the optimization. pycparser is needed for the
# cryptography package.
ENV PYTHONOPTIMIZE=
# Python: Warning control.
ENV PYTHONWARNINGS="ignore::DeprecationWarning"
# Django: Disable debug mode.
ENV DJANGO_DEBUG=False
#
# Web Application.
WORKDIR $APP_HOME
USER $APP_USER
COPY core ./core/
COPY core_health ./core_health/
COPY webapp ./webapp/
COPY VERSION manage.py deployment/gunicorn.sh deployment/gunicorn.conf.py ./
RUN WEBAPP_ENVIRONMENT="building" python manage.py collectstatic --no-input
ENTRYPOINT ["/bin/sh", "gunicorn.sh"]

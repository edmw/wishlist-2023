# Local Deploy Environment

This environment has mostly the same configuration as the environment "local" for development, except that it is set up as closely as possible with settings from the production environment.

This affects the application for which the deployment image instead of the development image is used, the webserver where gunicorn is used instead of the internal server and the logging which only logs warnings and errors.

# 2. Applications

Date: 2022-02-22

## Status

Accepted

## Context

In a Django project the term application describes a Python package that provides some set of features. Applications include some combination of models, views, templates, template tags, middlewares, and so on. 

## Decision

This project is divided into different applications, each of which is responsible for specific tasks:

* `webapp` -- the foundation for the project containing all the functionality that are not related to the business logic but for the execution as a web application.
* `core` -- the core of the project in which the actual business logic and its user interface resides.
* `core_health` -- an addition to the core of the project which is responsible for reporting the integrity of the application.

## Consequences

There is a clear separation of responsibilities between the different applications and the features of an individual application remain manageable.

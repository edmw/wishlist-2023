# 1. Record requirements

Date: 2026-11-08

## Status

Accepted

## Context

We record architectural decisions as ADRs, but the reasons behind them,
the needs and expectations that drive a feature, are not written down.
Without them, it is hard to tell later why a feature exists, what it must
achieve, and whether a decision still fits.

We need a plain and lightweight way to record requirements next to our ADRs.

## Requirements

* REQ-1.1: Each feature or larger change must have a requirements document
  before implementation starts.
* REQ-1.2: Each requirements document must be a single Markdown file in
  `documentation/`, numbered consecutively (`req-0001-title.md`).
* REQ-1.3: Each requirements document must have the sections Context,
  Requirements, Acceptance Criteria, Out of Scope and Related.
* REQ-1.4: Individual requirements must be numbered (`REQ-<doc>.<n>`) so
  that ADRs and tasks can refer to them.
* REQ-1.5: When a requirement affects the architecture, the resulting ADR
  must reference it, and the requirement must link back to the ADR.
* REQ-1.6: Requirements should be phrased in the form "The system must ..."
  or "When <trigger>, the system must <response>."
* REQ-1.7: Requirements documents should not be deleted. Obsolete ones
  get the status Superseded.

## Acceptance Criteria

* Given a new feature, when work begins, then a requirements document
  exists with status Proposed or Accepted.
* Given an ADR that results from a requirement, when reading the ADR,
  then the requirement number is mentioned in its Context.
* Given any requirement, when reading it, then it can be identified
  unambiguously by its number.

## Out of Scope

* Task planning.
* Tooling or automation for requirements.
* Requirements for bugfixes and trivial changes.

## Related

* ADR: [1. Record architecture decisions](adr-0001-record-architecture-decisions.md)

## Template

```
# N. Short title of the requirement

Date: YYYY-MM-DD

## Status

Proposed | Accepted | Implemented | Superseded | Rejected

## Context

Why is this needed? What problem does it solve, and for whom?

## Requirements

* REQ-N.1: The system must ...
* REQ-N.2: When <trigger>, the system must <response>.

## Acceptance Criteria

* Given <state>, when <action>, then <result>.

## Out of Scope

* ...

## Related

* ADR: [N. Title](../adr/000N-title.md)
```

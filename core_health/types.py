"""Types used by the Core Health application."""

from __future__ import annotations

from typing import NamedTuple, Sequence, Tuple, Union, overload, override


class HealthCheckResult(NamedTuple):
    """Represents the result of a single health check."""

    status: bool
    component_name: str
    check_id: int
    check_text: str

    def __str__(self) -> str:
        """Returns string representation for this check.

        Note: This representation is used for the plain text rendering of the
        check results.
        """
        return f"{str(self.status):6} [{self.component_name}][{self.check_id:04}] {self.check_text}"


class HealthCheckResults(list[HealthCheckResult]):
    """Represents the results of multiple health checks.

    This extension of the list type allows adding more results where
    the added results can be either real healh check result types or
    simple tuples. This is a convenience for other apps which do not
    need to import anything from this package, then.

    ```
    results = HealthCheckResults()
    results += [HealthCheckResult(...), ...]  # works
    results += [(True, 'any name', 1, 'any description'), ...]  # works, too
    ```
    """

    def _append(
        self,
        more: Sequence[HealthCheckResult] | Sequence[tuple[bool, str, int, str]],
    ) -> None:
        """Appends the given check results to self."""
        for result in more:
            if isinstance(result, HealthCheckResult):
                self.append(result)
            elif (
                type(result) is tuple
                and len(result) == 4
                and isinstance(result[0], bool)
                and isinstance(result[1], str)
                and isinstance(result[2], int)
                and isinstance(result[3], str)
            ):
                self.append(HealthCheckResult(*result))
            else:
                raise TypeError()

    @overload
    def __add__(self, more: Sequence[HealthCheckResult]) -> HealthCheckResults: ...

    @overload
    def __add__(self, more: Sequence[Tuple[bool, str, int, str]]) -> HealthCheckResults: ...

    @override
    def __add__(
        self,
        more: Sequence[Union[HealthCheckResult, Tuple[bool, str, int, str]]],
    ) -> HealthCheckResults:
        """Override magic `__add__` method to allow tuples to be added.
        Tuples will be converted to `HealthCheckResult` objects before adding.
        """
        self._append(more)
        return self

    @overload
    def __iadd__(self, more: Sequence[HealthCheckResult]) -> HealthCheckResults: ...

    @overload
    def __iadd__(self, more: Sequence[Tuple[bool, str, int, str]]) -> HealthCheckResults: ...

    @override
    def __iadd__(
        self,
        more: Sequence[Union[HealthCheckResult, Tuple[bool, str, int, str]]],
    ) -> HealthCheckResults:
        """Override magic `__iadd__` method to allow tuples to be added.
        Tuples will be converted to `HealthCheckResult` objects before adding.
        """
        self._append(more)
        return self

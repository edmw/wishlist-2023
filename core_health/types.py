"""Types used by the Core Health application."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Iterable, NamedTuple, Protocol, Tuple, overload, override


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


class HealthCheckResultsLike(Protocol):
    def __iter__(self) -> Iterator[Tuple[bool, str, int, str]]: ...


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

    @staticmethod
    def _coerce_item(item: object) -> HealthCheckResult:
        """Coerces the given item to a HealthCheckResult if possible.

        Raises:
            TypeError: If the given item cannot be coerced to a HealthCheckResult.
        """
        if isinstance(item, HealthCheckResult):
            return item
        elif (
            type(item) is tuple
            and len(item) == 4
            and isinstance(item[0], bool)
            and isinstance(item[1], str)
            and isinstance(item[2], int)
            and isinstance(item[3], str)
        ):
            return HealthCheckResult(*item)
        else:
            raise TypeError(f"Cannot coerce {item} to HealthCheckResult.")

    def extend(self, more: Iterable[HealthCheckResult] | HealthCheckResultsLike) -> None:
        for item in more:
            self.append(self._coerce_item(item))

    def added(self, more: Iterable[HealthCheckResult] | HealthCheckResultsLike) -> HealthCheckResults:
        result = HealthCheckResults(self)
        result.extend(more)
        return result

    @overload
    def __iadd__(self, more: Iterable[HealthCheckResult]) -> HealthCheckResults: ...

    @overload
    def __iadd__(self, more: HealthCheckResultsLike) -> HealthCheckResults: ...

    @override
    def __iadd__(
        self,
        more: Iterable[HealthCheckResult] | HealthCheckResultsLike,
    ) -> HealthCheckResults:
        """Override magic `__iadd__` method to allow tuples to be added.
        Tuples will be converted to `HealthCheckResult` objects before adding.
        """
        self.extend(more)
        return self

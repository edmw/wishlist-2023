from dataclasses import dataclass
from pathlib import Path
from typing import Final

PROJECT_NAME = "wishlist-webapp"


@dataclass(frozen=True)
class Paths:
    PROJECT: Final[Path] = Path(__file__).resolve().parent.parent.parent
    REPORTS: Final[Path] = PROJECT / "reports"
    REPORTS_COVERAGE: Final[Path] = REPORTS / "coverage"
    REPORTS_COVERAGE_HTML: Final[Path] = REPORTS_COVERAGE / "html"
    ENV_LOCAL: Final[Path] = PROJECT / "environments" / "local"
    ENV_LOCAL_DEPLOY: Final[Path] = PROJECT / "environments" / "local-deploy"
    ENV_TESTING: Final[Path] = PROJECT / "environments" / "testing"
    ENV_COMMON: Final[Path] = PROJECT / "environments" / "common"
    ENV_PRIVATE: Final[Path] = PROJECT / "private" / "environments"
    ENV_PRIVATE_LOCAL: Final[Path] = ENV_PRIVATE / "local"
    ENV_PRIVATE_LOCAL_DEPLOY: Final[Path] = ENV_PRIVATE / "local-deploy"

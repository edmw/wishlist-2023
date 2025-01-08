from enum import Enum


class Color(Enum):
    TEXT_INFO = "sky_blue1"
    TEXT_OK = "green"
    TEXT_NOT_OK = "indian_red1"
    TEXT_PROBLEMATIC = "orange1"

    BOX_H1 = "white"
    BOX_H2 = "white"
    BOX_H3 = "gray30"

    def markup(self, text: str) -> str:
        return f"[bold {self.value}]{text}[/bold {self.value}]"

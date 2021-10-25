from typing import Optional
from enum import Enum
from datetime import time


def round_minute(minute: int, second: int) -> int:
    return minute if second < 30 else minute + 1


def round_hour(hour: int, minute: int) -> int:
    return round_minute(hour, minute)


class Time(time):
    class Format(Enum):
        BLOG = 1

    @staticmethod
    def from_seconds(number: float) -> "Time":
        hours = divmod(number, 3600)
        minutes = divmod(hours[1], 60)
        seconds = minutes[1]
        microseconds = (
            ((number - int(number)) * 1_000_000) if type(number) is float else 0
        )

        return Time(int(hours[0]), int(minutes[0]), int(seconds), int(microseconds))

    def format_(self, format_: "Time.Format" = Format.BLOG) -> Optional[str]:
        if format_ == Time.Format.BLOG:
            if self.minute == 0 and self.hour == 0:
                return (
                    f"{self.second} " f"{'Second' if self.second == 1 else 'Seconds'}"
                )
            elif self.hour == 0 and self.minute > 0:
                minute = round_minute(self.minute, self.second)
                return f"{minute} {'Minute' if minute == 1 else 'Minutes'}"
            elif self.hour > 0:
                hour = round_hour(self.hour, self.minute)
                minute = round_minute(self.minute, self.second)
                return (
                    f"{hour} {'Hour' if hour == 1 else 'Hours'} {minute} "
                    f"{'Minute' if minute == 1 else 'Minutes'}"
                )
            return "∞ Millennia"
        return None

    def __add__(self, other: time) -> "Time":
        if type(other) in (Time, time):
            # The default constructor of datetime.time enforces ranges for
            # minutes, seconds, and microseconds
            return Time.from_seconds(
                (self.hour + other.hour) * 3600
                + (self.minute + other.minute) * 60
                + (self.second + other.second)
                + (self.microsecond + other.microsecond) / 1_000_000
            )
        return NotImplemented

    def __str__(self) -> str:
        return self.format_() or ""

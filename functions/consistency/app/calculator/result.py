from dataclasses import dataclass, field
from typing import Counter
from collections import Counter as C


@dataclass
class ConsistencyResult:
    p5: float
    p6: float
    rescued_5: int = 0
    rescued_6: int = 0
    useful_gambles: Counter[int] = field(default_factory=C)
    failed_gambles_5: int = 0
    failed_gambles_6: int = 0


@dataclass
class HandTestResult:
    matches_without_gambling: bool
    matches_with_gambling: bool
    rescued_with_gambling: int = 0
    useful_gambles: Counter[int] = field(default_factory=Counter)
    failed_gamble_attempts: int = 0

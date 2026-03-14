from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ConsistencyResult:
    p5: float
    p6: float


@dataclass
class HandTestResult:
    matches_without_gambling: bool
    matches_with_gambling: bool

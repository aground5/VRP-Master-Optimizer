"""
Labor & Operations Domain Models.

Encapsulates work rules, shift definitions, and break policies.
"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class BreakRule:
    """Defines mandatory break requirements."""
    interval_minutes: int = 240  # Break required after X minutes of driving
    duration_minutes: int = 30   # Break lasts Y minutes
    
@dataclass
class WorkShift:
    """Defines a work shift window for a driver/vehicle."""
    start_time: int = 0          # Shift start (in time units, e.g., minutes from midnight)
    max_duration: int = 720      # Maximum allowed shift duration (12 hours)
    standard_duration: int = 480 # Standard (non-overtime) duration (8 hours)

@dataclass
class LaborCost:
    """Cost parameters related to labor/time."""
    regular_rate: int = 10       # Cost per minute of regular work
    overtime_multiplier: float = 1.5  # Overtime pays X times regular
    
@dataclass
class LaborPolicy:
    """Aggregates all labor-related rules."""
    shift: WorkShift = field(default_factory=WorkShift)
    break_rule: BreakRule = field(default_factory=BreakRule)
    cost: LaborCost = field(default_factory=LaborCost)

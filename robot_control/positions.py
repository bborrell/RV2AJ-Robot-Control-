"""Data structures representing robot positions and joint angles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class JointPosition:
    """Joint space position for the RV-2AJ (6-axis).

    All angles are expressed in degrees.

    Attributes:
        j1: Rotation about axis 1 (waist), degrees.
        j2: Rotation about axis 2 (shoulder), degrees.
        j3: Rotation about axis 3 (elbow), degrees.
        j4: Rotation about axis 4 (wrist pitch), degrees.
        j5: Rotation about axis 5 (wrist roll), degrees.
        j6: Rotation about axis 6 (wrist yaw), degrees.
    """

    j1: float = 0.0
    j2: float = 0.0
    j3: float = 0.0
    j4: float = 0.0
    j5: float = 0.0
    j6: float = 0.0

    def as_list(self) -> List[float]:
        """Return joint angles as an ordered list [j1 .. j6]."""
        return [self.j1, self.j2, self.j3, self.j4, self.j5, self.j6]

    def __str__(self) -> str:
        return (
            f"J1={self.j1:.3f}, J2={self.j2:.3f}, J3={self.j3:.3f}, "
            f"J4={self.j4:.3f}, J5={self.j5:.3f}, J6={self.j6:.3f}"
        )


@dataclass
class CartesianPosition:
    """Cartesian (tool-frame) position for the RV-2AJ.

    Linear units are millimetres; rotational units are degrees.

    Attributes:
        x: X coordinate, mm.
        y: Y coordinate, mm.
        z: Z coordinate, mm.
        rx: Rotation about X axis (roll), degrees.
        ry: Rotation about Y axis (pitch), degrees.
        rz: Rotation about Z axis (yaw), degrees.
        configuration: Robot configuration flags (FL1/FL2/FL3).
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0
    ry: float = 0.0
    rz: float = 0.0
    configuration: str = "7"

    def __str__(self) -> str:
        return (
            f"X={self.x:.3f}, Y={self.y:.3f}, Z={self.z:.3f}, "
            f"Rx={self.rx:.3f}, Ry={self.ry:.3f}, Rz={self.rz:.3f} [{self.configuration}]"
        )


# ---------------------------------------------------------------------------
# Joint limits for RV-2AJ (degrees) – from the hardware manual
# ---------------------------------------------------------------------------
JOINT_LIMITS: List[dict] = [
    {"axis": "J1", "min": -240.0, "max": 240.0},
    {"axis": "J2", "min": -115.0, "max": 115.0},
    {"axis": "J3", "min": -70.0,  "max": 165.0},
    {"axis": "J4", "min": -200.0, "max": 200.0},
    {"axis": "J5", "min": -115.0, "max": 115.0},
    {"axis": "J6", "min": -360.0, "max": 360.0},
]

# Home position (all axes at 0 degrees)
HOME_POSITION = JointPosition(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

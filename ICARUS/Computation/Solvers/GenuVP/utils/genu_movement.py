from typing import Any

from ICARUS.Core.types import FloatArray
from ICARUS.Flight_Dynamics.disturbances import Disturbance
from ICARUS.Vehicle.wing_segment import Wing_Segment


class Movement:
    """
    Class to specify a generalized Movement as defined in the gnvp3 manual.
    """

    def __init__(
        self,
        name: str,
        Rotation: dict[str, Any],
        Translation: dict[str, Any],
    ) -> None:
        """
        Initialize the Movement Class

        Args:
            name (str): Name of the Movement
            Rotation (dict[str,Any]): Rotation Parameters. They must include:\
                                        1) type: int \
                                        2) axis: int \
                                        3) t1: float \
                                        4) t2: float \
                                        5) a1: float \
                                        6) a2: float \
            Translation (dict[str,Any]): Translation Parameters. They must include: \
                                        1) type: int \
                                        2) axis: int \
                                        3) t1: float \
                                        4) t2: float \
                                        5) a1: float \
                                        6) a2: float \
        """
        self.name: str = name
        self.rotation_type: int = Rotation["type"]

        self.rotation_axis: int = Rotation["axis"]

        self.rot_t1: float = Rotation["t1"]
        self.rot_t2: float = Rotation["t2"]

        self.rot_a1: float = Rotation["a1"]
        self.rot_a2: float = Rotation["a2"]

        self.translation_type: int = Translation["type"]

        self.translation_axis: int = Translation["axis"]

        self.translation_t1: float = Translation["t1"]
        self.translation_t2: float = Translation["t2"]

        self.translation_a1: float = Translation["a1"]
        self.translation_a2: float = Translation["a2"]


def distrubance2movement(disturbance: Disturbance) -> Movement:
    """
    Converts a disturbance to a movement

    Args:
        disturbance (Disturbance): Disturbance Object

    Raises:
        ValueError: If the disturbance type is not supported

    Returns:
        Movement: Movement Object
    """
    if disturbance.type == "Derivative":
        t1: float = -1
        t2: float = 0
        a1: float | None = 0
        a2: float | None = disturbance.amplitude
        distType = 8
    elif disturbance.type == "Value":
        t1 = -1
        t2 = 0.0
        a1 = disturbance.amplitude
        a2 = disturbance.amplitude
        distType = 1
    else:
        raise ValueError

    undisturbed: dict[str, Any] = {
        "type": 1,
        "axis": disturbance.axis,
        "t1": -1,
        "t2": 0,
        "a1": 0,
        "a2": 0,
    }

    disturbed: dict[str, Any] = {
        "type": distType,
        "axis": disturbance.axis,
        "t1": t1,
        "t2": t2,
        "a1": a1,
        "a2": a2,
    }

    if disturbance.isRotational:
        Rotation: dict[str, Any] = disturbed
        Translation: dict[str, Any] = undisturbed
    else:
        Rotation = undisturbed
        Translation = disturbed

    return Movement(disturbance.name, Rotation, Translation)


def define_movements(
    surfaces: list[Wing_Segment],
    CG: FloatArray,
    orientation: FloatArray | list[float],
    disturbances: list[Disturbance] = [],
) -> list[list[Movement]]:
    """
    Define Movements for the surfaces.

    Args:
        surfaces (list[Wing]): List of Wing Objects
        CG (FloatArray): Center of Gravity
        orientation (FloatArray | list[float]): Orientation of the plane
        disturbances (list[Disturbance]): List of possible Disturbances. Defaults to empty list.

    Returns:
        list[list[Movement]]: A list of movements for each surface of the plane so that the center of gravity is at the origin.
    """
    movement: list[list[Movement]] = []
    all_axes = ("pitch", "roll", "yaw")
    all_ax_ids = (2, 1, 3)
    for _ in surfaces:
        sequence: list[Movement] = []
        for name, axis in zip(all_axes, all_ax_ids):
            Rotation: dict[str, Any] = {
                "type": 1,
                "axis": axis,
                "t1": -0.1,
                "t2": 0.0,
                "a1": orientation[axis - 1],
                "a2": orientation[axis - 1],
            }
            Translation: dict[str, Any] = {
                "type": 1,
                "axis": axis,
                "t1": -0.1,
                "t2": 0.0,
                "a1": -CG[axis - 1],
                "a2": -CG[axis - 1],
            }

            obj = Movement(name, Rotation, Translation)
            sequence.append(obj)

        for disturbance in disturbances:
            if disturbance.type is not None:
                sequence.append(distrubance2movement(disturbance))

        movement.append(sequence)
    return movement

import numpy as np

from ICARUS.Core.types import FloatArray
from ICARUS.Database.utils import angle_to_case
from ICARUS.Software.GenuVP3.postProcess.getWakeData import get_wake_data
from ICARUS.Visualization.GNVPwake import gnvp_wake


def gnvp_geometry(plot: bool = False) -> tuple[list[FloatArray], list[FloatArray]]:
    """
    Get the geometry from the gnvp results and the airplane. Has to convert to meshgrid to be able to
    sort the data.

    Args:
        plot (bool, optional): If True it plots the result. Defaults to False.

    Returns:
        tuple[list[FloatArray], list[FloatArray]]: Meshgrid of the geometry from the gnvp results and the airplane.
    """
    from Data.Planes.simple_wing import airplane

    # Get the Case Name
    case: str = angle_to_case(2.0)
    # Get the grid data from the gnvp results
    _, _, grid_gnvp = get_wake_data(airplane, case)
    mesh_grid_gnvp: list[FloatArray] = np.meshgrid(
        grid_gnvp,
    )  # converts the array to a meshgrid

    # Get the grid data from the airplane
    lgrid_plane: list[FloatArray] = []
    for surface in airplane.surfaces:
        lgrid_plane.append(surface.getGrid())  # loads the grid data from each surface
    grid_plane: FloatArray = np.array(lgrid_plane)  # converts the list to a numpy array
    shape = grid_plane.shape  # gets the shape of the array
    grid_plane = (
        grid_plane.reshape(shape[0] * shape[1] * shape[2], shape[3]) - airplane.CG
    )  # reshapes the array to a 2D array and subtracts the CG
    mesh_grid_plane: list[FloatArray] = np.meshgrid(
        grid_plane,
    )  # converts the array to a meshgrid

    if plot:
        gnvp_wake(airplane, case)
    return mesh_grid_plane, mesh_grid_gnvp

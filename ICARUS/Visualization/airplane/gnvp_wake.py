import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

from ICARUS.Computation.Solvers.GenuVP.post_process.wake import get_wake_data_3
from ICARUS.Computation.Solvers.GenuVP.post_process.wake import get_wake_data_7
from ICARUS.Database.utils import angle_to_case
from ICARUS.Vehicle.plane import Airplane


def plot_gnvp3_wake(plane: Airplane, case: str, scale: str = "True", figsize: tuple[int, int] = (16, 7)) -> None:
    plot_gnvp_wake(gnvp_version=3, plane=plane, case=case, scale=scale, figsize=figsize)


def plot_gnvp7_wake(plane: Airplane, case: str, scale: str = "True", figsize: tuple[int, int] = (16, 7)) -> None:
    plot_gnvp_wake(gnvp_version=7, plane=plane, case=case, scale=scale, figsize=figsize)


def plot_gnvp_wake(
    gnvp_version: int,
    plane: Airplane,
    case: str,
    scale: str = "True",
    figsize: tuple[int, int] = (16, 7),
) -> None:
    """
    Visualize the wake of a given plane

    Args:
        plane (Airplane): Plane Object
        case (str): Case Name
        scale (str): Whether to plot on a true scale or not
        figsize (tuple[int,int]): Figure Size. Defaults to (16, 7).
    """

    if gnvp_version == 3:
        get_wake_data = get_wake_data_3
    elif gnvp_version == 7:
        get_wake_data = get_wake_data_7
    else:
        raise ValueError(f"GNVP Version error! Got Version {gnvp_version} ")

    A1, B1, C1 = get_wake_data(plane, case)

    fig: Figure = plt.figure(figsize=figsize)
    ax: Axes3D = fig.add_subplot(projection="3d")

    ax.set_title(f"{plane.name} wake with GNVP{gnvp_version} for case {case}")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.view_init(30, 150)
    ax.axis("scaled")
    ax.set_xlim(-plane.span / 2, plane.span / 2)
    ax.set_ylim(-plane.span / 2, plane.span / 2)
    ax.set_zlim(-1, 1)

    ax.scatter(A1[:, 0], A1[:, 1], A1[:, 2], color="r", s=5)  # WAKE
    ax.scatter(B1[:, 0], B1[:, 1], B1[:, 2], color="k", s=5)  # NEARWAKE
    ax.scatter(C1[:, 0], C1[:, 1], C1[:, 2], color="g", s=5)  # GRID

    plane.visualize(fig, ax, movement=-np.array(plane.CG))
    if scale == "True":
        ax.set_aspect("equal", "box")
    plt.show()


# def gnvp_wake_video(plane: Airplane, case: str, figsize=(16, 7)) -> None:
#     """
#     TODO: Make a video of the wake

#     Args:
#         plane (Airplane): Plane Object
#         case (str): Case Name
#         figsize (tuple, optional): Figure Size. Defaults to (16, 7).
#     """
#     pass

if __name__ == "__main__":
    ## In the folder we are working on
    import os

    folder_name: str = os.path.basename(os.getcwd())
    print(folder_name)

    from ICARUS.Database import DB

    print(DB.vehicles_db.get_planenames())
    if folder_name in DB.vehicles_db.get_planenames():
        plane: Airplane = DB.vehicles_db.planes[folder_name]
    else:
        print(f"Plane {folder_name} not found in the database")
        exit()

    # Read from sys.argv
    # arg -g is the genu version
    # arg -a is the angle of attack

    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gnvp", type=int, default=3, help="Genu Version")
    parser.add_argument("-a", "--angle", type=float, default=2.0, help="Angle of Attack")
    args = parser.parse_args()
    gnvp_version: int = args.gnvp
    case: float = args.angle

    case_str: str = angle_to_case(case)
    if gnvp_version == 3:
        plot_gnvp3_wake(plane, case_str)
    elif gnvp_version == 7:
        plot_gnvp7_wake(plane, case_str)
    else:
        print(f"GNVP Version error! Got Version {gnvp_version} ")
        exit()

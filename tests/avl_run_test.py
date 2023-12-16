import time

import numpy as np

from ICARUS.Computation.Solvers.solver import Solver
from ICARUS.Core.struct import Struct
from ICARUS.Core.types import FloatArray
from ICARUS.Flight_Dynamics.state import State
from ICARUS.Vehicle.plane import Airplane


def avl_run() -> None:
    print("Testing AVL Running ...")
    # Get Plane, DB
    from examples.Vehicles.Planes.benchmark_plane import get_bmark_plane

    bmark, state = get_bmark_plane("bmark")

    # Get Solver
    from ICARUS.Computation.Solvers.AVL.avl import AVL

    avl: Solver = AVL()
    analysis: str = avl.get_analyses_names()[0]

    avl.select_analysis(analysis)

    # Set Options
    options: Struct = avl.get_analysis_options(verbose=True)

    AoAmin = -3
    AoAmax = 3
    NoAoA = (AoAmax - AoAmin) + 1
    angles_all: FloatArray = np.linspace(AoAmin, AoAmax, NoAoA)
    angles: list[float] = [ang for ang in angles_all]

    options.plane = bmark
    options.state = state
    options.solver2D = "XFLR"
    options.angles = angles

    avl.set_analysis_options(options)
    _ = avl.get_analysis_options(verbose=True)
    start_time: float = time.perf_counter()

    avl.execute()

    end_time: float = time.perf_counter()
    print(f"AVL Run took: --- %s seconds ---" % (end_time - start_time))
    print("Testing AVL Running... Done")

    _ = avl.get_results()
    bmark.save()

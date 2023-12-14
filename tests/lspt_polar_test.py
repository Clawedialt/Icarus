import time

import numpy as np

from ICARUS.Computation.Solvers.solver import Solver
from ICARUS.Core.struct import Struct
from ICARUS.Core.types import FloatArray
from ICARUS.Flight_Dynamics.state import State
from ICARUS.Vehicle.plane import Airplane


def lspt_run() -> None:
    print("Testing LSPT Running...")

    # Get Plane, DB
    from examples.Vehicles.Planes.benchmark_plane import get_bmark_plane

    airplane: Airplane = get_bmark_plane("bmark")

    # Get Environment
    from ICARUS.Environment.definition import EARTH_ISA

    u_freestream = 20
    state = State(
        name="Unstick",
        airplane=airplane,
        environment=EARTH_ISA,
        u_freestream=u_freestream,
    )
    # Get Solver
    from ICARUS.Computation.Solvers.Icarus_LSPT.wing_lspt import get_lspt

    lspt: Solver = get_lspt()

    # Set Analysis
    analysis: str = lspt.available_analyses_names()[0]

    lspt.set_analyses(analysis)

    # Set Options
    options: Struct = lspt.get_analysis_options(verbose=True)
    solver_parameters: Struct = lspt.get_solver_parameters()

    AoAmin = -3
    AoAmax = 3
    NoAoA = (AoAmax - AoAmin) + 1
    angles: FloatArray = np.linspace(AoAmin, AoAmax, NoAoA)

    options.plane.value = airplane
    options.state.value = state
    options.solver2D.value = "Xfoil"
    options.angles.value = angles

    solver_parameters.Ground_Effect.value = True
    solver_parameters.Wake_Geom_Type.value = "TE-Geometrical"

    _ = lspt.get_analysis_options(verbose=True)
    start_time: float = time.perf_counter()

    lspt.run()

    end_time: float = time.perf_counter()
    print(f"LSPT Run took: --- %s seconds ---" % (end_time - start_time))
    print("Testing GNVP Running... Done")

    _ = lspt.get_results()
    airplane.save()
from typing import Any

from ICARUS.Airfoils.airfoil import Airfoil
from ICARUS.Computation.Analyses.analysis import Analysis
from ICARUS.Computation.Solvers.OpenFoam.analyses.angles import angles_parallel
from ICARUS.Computation.Solvers.OpenFoam.analyses.angles import angles_serial
from ICARUS.Computation.Solvers.OpenFoam.files.setup_case import MeshType
from ICARUS.Computation.Solvers.solver import Solver


def get_open_foam() -> Solver:
    open_foam = Solver(name="open_foam", solver_type="CFD", fidelity=3)

    options: dict[str, tuple[str, Any]] = {
        "airfoil": (
            "Airfoil to run",
            Airfoil,
        ),
        "reynolds": (
            "List of Reynolds numbers to run",
            list[float],
        ),
        "mach": (
            "Mach number",
            float,
        ),
        "angles": (
            "angles to run",
            list[float],
        ),
    }

    solver_options: dict[str, tuple[Any, str, Any]] = {
        "mesh_type": (
            MeshType.structAirfoilMesher,
            "Type of mesh to use",
            MeshType,
        ),
        "max_iterations": (
            400,
            "Maximum number of iterations",
            int,
        ),
        "silent": (
            1e-3,
            "Whether to print progress or not",
            float,
        ),
    }

    aoa_simple_struct_serial: Analysis = Analysis(
        solver_name="open_foam",
        analysis_name="SIMPLE with structured Mesh sequentially",
        run_function=angles_serial,
        options=options,
        solver_options=solver_options,
        unhook=None,
    )

    aoa_simple_struct_parallel: Analysis = Analysis(
        solver_name="open_foam",
        analysis_name="Simple with structured Mesh in parallel",
        run_function=angles_parallel,
        options=options,
        solver_options=solver_options,
        unhook=None,
    )

    open_foam.add_analyses(
        [
            aoa_simple_struct_parallel,
            aoa_simple_struct_serial,
        ],
    )

    return open_foam


if __name__ == "__main__":
    open_foam = get_open_foam()

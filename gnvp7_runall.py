"""
Module to run multiple 3D simulations for different aircrafts sequentially.
It computes the polars for each aircraft and then computes the dynamics.
It is also possible to do a pertubation analysis for each aircraft.
"""
import time
from typing import Any

import numpy as np
from numpy import dtype
from numpy import floating
from numpy import ndarray
from pandas import DataFrame

from examples.Planes.e190_cruise import e190_cruise
from examples.Planes.e190_takeoff import e190_takeoff
from examples.Planes.hermes import hermes
from examples.Planes.hermes_wing_only import hermes_main_wing
from examples.Planes.wing_variations import wing_var_chord_offset
from ICARUS.Core.struct import Struct
from ICARUS.Database import XFLRDB
from ICARUS.Database.Database_2D import Database_2D
from ICARUS.Database.db import DB
from ICARUS.Enviroment.definition import EARTH
from ICARUS.Flight_Dynamics.state import State
from ICARUS.Input_Output.XFLR5.parser import parse_xfl_project
from ICARUS.Input_Output.XFLR5.polars import read_polars_2d
from ICARUS.Solvers.Airplane.gnvp7 import get_gnvp7
from ICARUS.Vehicle.plane import Airplane
from ICARUS.Workers.solver import Solver


def main() -> None:
    """Main function to run the simulations."""
    start_time: float = time.time()

    # # DB CONNECTION
    db = DB()
    db.load_data()
    airfoils = db.foilsDB.airfoils
    foildb: Database_2D = db.foilsDB
    foildb.load_data()
    read_polars_2d(foildb, XFLRDB)

    # # Get Plane
    planes: list[Airplane] = []

    # planes.append(wing_var_chord_offset(airfoils, "orthogonal_7", [0.159, 0.159], 0.0))

    # planes.append(
    #     wing_var_chord_offset(airfoils, "orthSweep_7", [0.32, 0.32], 0.001),
    # )

    # planes.append(wing_var_chord_offset(airfoils, "taperSweep_7", [0.159, 0.072], 0.2))

    # planes.append(wing_var_chord_offset(airfoils, "taper_7", [0.159, 0.072], 0.0))

    # planes.append(hermes(airfoils=airfoils, name='hermes_7'))
    # planes[0].CG = -np.array([0.032, 0., 0.001301])
    timestep: dict[str, float] = {
        "orthogonal_7": 1e-3,
        "orthSweep_7": 1e-3,
        "taperSweep_7": 1e-3,
        "taper_7": 1e-3,
        "atlas_7": 1e-3,
        "hermes_7": 1e-2,
        "e190_to_7": 100,
        "e190_cr_7": 100,
    }
    maxiter: dict[str, int] = {
        "orthogonal_7": 100,
        "orthSweep_7": 100,
        "taperSweep_7": 400,
        "taper_7": 400,
        "atlas_7": 400,
        "hermes_7": 20,
        "e190_to_7": 200,
        "e190_cr_7": 200,
    }

    UINF: dict[str, float] = {
        "e190_to_7": 20,
        "e190_cr_7": 232,
    }

    DENS: dict[str, float] = {
        "e190_to_7": 1.225,
        "e190_cr_7": 0.538,
    }

    # embraer.name = "embraer_3"
    embraer_to: Airplane = e190_takeoff(name="e190_to_7")
    embraer_cr: Airplane = e190_cruise(name="e190_cr_7")

    # embraer.visualize()
    planes.append(embraer_to)
    planes.append(embraer_cr)

    for airplane in planes:
        print("--------------------------------------------------")
        print(f"Running {airplane.name}")
        print("--------------------------------------------------")

        # # Import Enviroment
        EARTH.air_density = DENS[airplane.name]
        print(EARTH)

        # # Get Solver
        gnvp7: Solver = get_gnvp7(db)

        # ## AoA Run
        # 0: Single Angle of Attack (AoA) Run
        # 1: Angles Sequential
        # 2: Angles Parallel

        analysis: str = gnvp7.available_analyses_names()[1]
        gnvp7.set_analyses(analysis)
        options: Struct = gnvp7.get_analysis_options(verbose=False)
        solver_parameters: Struct = gnvp7.get_solver_parameters()

        AOA_MIN = -6
        AOA_MAX = 6
        NO_AOA: int = (AOA_MAX - AOA_MIN) + 1
        angles: ndarray[Any, dtype[floating[Any]]] = np.linspace(
            AOA_MIN,
            AOA_MAX,
            NO_AOA,
        )
        # UINF = 223
        airplane.define_dynamic_pressure(UINF[airplane.name], EARTH.air_density)

        options.plane.value = airplane
        options.environment.value = EARTH
        options.db.value = db
        options.solver2D.value = "Xfoil"
        options.maxiter.value = maxiter[airplane.name]
        options.timestep.value = timestep[airplane.name]
        options.u_freestream.value = UINF[airplane.name]
        options.angles.value = angles

        solver_parameters.Use_Grid.value = True
        solver_parameters.Split_Symmetric_Bodies.value = False

        gnvp7.print_analysis_options()

        polars_time: float = time.time()
        gnvp7.run()
        print(
            f"Polars took : --- {time.time() - polars_time} seconds --- in Parallel Mode",
        )
        polars: DataFrame | int = gnvp7.get_results()
        airplane.save()
        if isinstance(polars, int):
            continue
        continue
        # # Dynamics
        # ### Define and Trim Plane
        try:
            unstick = State("Unstick", airplane, polars, EARTH)
        except Exception as error:
            print(error)
            continue

        # ### Pertrubations
        # epsilons = {
        #     "u": 0.01,
        #     "w": 0.01,
        #     "q": 0.001,
        #     "theta": 0.01 ,
        #     "v": 0.01,
        #     "p": 0.001,
        #     "r": 0.001,
        #     "phi": 0.001
        # }
        epsilons = None

        unstick.add_all_pertrubations("Central", epsilons)
        unstick.get_pertrub()

        # Define Analysis for Pertrubations
        analysis = gnvp7.available_analyses_names()[3]  # Pertrubations PARALLEL
        print(f"Selecting Analysis: {analysis}")
        gnvp7.set_analyses(analysis)

        options = gnvp7.get_analysis_options(verbose=False)

        if options is None:
            raise ValueError("Options not set")
        # Set Options
        options.plane.value = airplane
        options.state.value = unstick
        options.environment.value = EARTH
        options.db.value = db
        options.solver2D.value = "Foil2Wake"
        options.maxiter.value = maxiter[airplane.name]
        options.timestep.value = timestep[airplane.name]
        options.u_freestream.value = unstick.trim["U"]
        options.angle.value = unstick.trim["AoA"]

        # Run Analysis
        gnvp7.print_analysis_options()

        pert_time: float = time.time()
        print("Running Pertrubations")
        gnvp7.run()
        print(f"Pertrubations took : --- {time.time() - pert_time} seconds ---")

        # Get Results And Save
        _ = gnvp7.get_results()
        unstick.save()

        # Sensitivity ANALYSIS
        # ADD SENSITIVITY ANALYSIS

    # print time program took
    print("PROGRAM TERMINATED")
    print(f"Execution took : --- {time.time() - start_time} seconds ---")


if __name__ == "__main__":
    main()
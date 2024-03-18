import os
import time

import numpy as np

from ICARUS.Airfoils.airfoil import Airfoil
from ICARUS.Computation.Solvers.OpenFoam.files.setup_case import MeshType
from ICARUS.Computation.Solvers.solver import Solver
from ICARUS.Computation.Solvers.XFLR5.polars import read_polars_2d
from ICARUS.Core.struct import Struct
from ICARUS.Core.types import FloatArray
from ICARUS.Core.units import calc_reynolds
from ICARUS.Database import DB
from ICARUS.Database import DB2D
from ICARUS.Database import EXTERNAL_DB


def main() -> None:
    """Main function to run multiple airfoil simulations"""
    start_time: float = time.time()

    # SETUP DB CONNECTION
    read_polars_2d(EXTERNAL_DB)

    # RUN SETUP
    calcXFoil: bool = True
    calcF2W: bool = False
    calcOpenFoam: bool = False

    print("Running:")
    print(f"\tFoil2Wake section: {calcF2W}")
    print(f"\tXfoil: {calcXFoil}")
    print(f"\tOpenfoam: {calcOpenFoam}")

    # LOAD AIRFOILS

    # airfoil_names: list[str] = ["0015", "0008", "0012", "2412", "4415"]
    # airfoil_names: list[str] = ["2412", "4415"]

    # Load From DB
    DB.load_data()

    all_airfoils = list(DB.foils_db.airfoils.keys())
    airfoils_to_compute = [
        airfoil
        for airfoil in all_airfoils
        if (
            airfoil.upper().startswith('AG')
            or airfoil.upper().startswith('CLARK')
            or airfoil.upper().startswith('DAE')
            or airfoil.upper().startswith('E')
            or airfoil.upper().startswith('H')
            or airfoil.upper().startswith('M')
            or airfoil.upper().startswith('N')
            or airfoil.upper().startswith('O')
            or airfoil.upper().startswith('S')
            or airfoil.upper().startswith('W')
        )
    ]
    print(f"Total number of loaded airfoils {len(list(DB.foils_db.airfoils.keys()))}")
    print(f"Total number of computed airfoil data {len(list(DB.foils_db._data.keys()))}")
    print(f"Total number of computed airfoil polars {len(list(DB.foils_db.polars.keys()))}")
    print(f"Computing: {len(airfoils_to_compute)}")

    # PARAMETERS FOR ESTIMATION
    chord_max: float = 0.5
    chord_min: float = 0.1
    u_max: float = 35.0
    u_min: float = 5.0
    viscosity: float = 1.56e-5

    # MACH ESTIMATION
    mach_max: float = 0.085
    # mach_min: float = calc_mach(10, speed_of_sound)
    # mach: FloatArray = np.linspace(mach_max, mach_min, 10)
    MACH: float = mach_max

    # REYNOLDS ESTIMATION
    reynolds_max: float = calc_reynolds(u_max, chord_max, viscosity)
    reynolds_min: float = calc_reynolds(u_min, chord_min, viscosity)
    reynolds: FloatArray = np.linspace(
        start=reynolds_min,
        stop=reynolds_max,
        num=5,
    )

    # ANGLE OF ATTACK SETUP
    aoa_min: float = -8
    aoa_max: float = 14
    num_of_angles: int = int((aoa_max - aoa_min) * 2 + 1)
    angles: FloatArray = np.linspace(
        start=aoa_min,
        stop=aoa_max,
        num=num_of_angles,
    )

    # Transition to turbulent Boundary Layer
    ftrip_up: dict[str, float] = {"pos": 0.1, "neg": 1.0}
    ftrip_low: dict[str, float] = {"pos": 0.1, "neg": 1.0}
    Ncrit = 9

    #   ############################## START LOOP ###########################################
    for airfoil_name in airfoils_to_compute:
        # Get airfoil
        airfoil: Airfoil = DB.foils_db.airfoils[airfoil_name]
        airfoil_stime: float = time.time()
        print(f"\nRunning airfoil {airfoil.name}\n")
        # airfoil.plot()
        airfoil.repanel(100, distribution='cosine')

        # Foil2Wake
        if calcF2W:
            f2w_stime: float = time.time()
            from ICARUS.Computation.Solvers.Foil2Wake.f2w_section import Foil2Wake

            f2w_s: Solver = Foil2Wake()

            analysis: str = f2w_s.get_analyses_names()[1]  # Multiple Reynolds
            f2w_s.select_analysis(analysis)
            f2w_options: Struct = f2w_s.get_analysis_options()
            f2w_solver_parameters: Struct = f2w_s.get_solver_parameters()

            # Set Options
            f2w_options.airfoil = airfoil
            f2w_options.reynolds = reynolds
            f2w_options.mach = MACH
            f2w_options.angles = angles
            f2w_s.print_analysis_options()

            f2w_solver_parameters.f_trip_upper = 0.1
            f2w_solver_parameters.f_trip_low = 0
            f2w_solver_parameters.Ncrit = Ncrit
            f2w_solver_parameters.max_iter = 250
            f2w_solver_parameters.boundary_layer_solve_time = 249  # IF STEADY SHOULD BE 1 LESS THAN MAX ITER
            f2w_solver_parameters.timestep = 0.1

            f2w_s.define_analysis(f2w_options, f2w_solver_parameters)
            f2w_s.execute(parallel=True)

            _ = f2w_s.get_results()
            f2w_etime: float = time.time()

            try:
                # Get polar
                polar = DB.foils_db.get_polars(airfoil.name, "Foil2Wake")

                airfoil_folder = os.path.join("Data/images/")
                polar.save_polar_plot_img(airfoil_folder, 'f2w')
            except Exception as e:
                print(f"Error saving polar plot. Got: {e}")

            print(f"Foil2Wake completed in {f2w_etime - f2w_stime} seconds")
        # XFoil
        if calcXFoil:
            xfoil_stime: float = time.time()
            from ICARUS.Computation.Solvers.Xfoil.xfoil import Xfoil

            xfoil: Solver = Xfoil()

            # Import Analysis
            # 0) Sequential Angle run for multiple reynolds with zeroing of the boundary layer between angles,
            # 1) Sequential Angle run for multiple reynolds
            analysis = xfoil.get_analyses_names()[1]  # Run
            xfoil.select_analysis(analysis)

            # Get Options
            xfoil_options: Struct = xfoil.get_analysis_options()
            xfoil_solver_parameters: Struct = xfoil.get_solver_parameters()

            # Set Options
            xfoil_options.airfoil = airfoil
            xfoil_options.reynolds = reynolds
            xfoil_options.mach = MACH
            xfoil_options.max_aoa = aoa_max
            xfoil_options.min_aoa = aoa_min
            xfoil_options.aoa_step = 0.5
            # xfoil_options.angles = angles  # For options 2 and 3

            xfoil.print_analysis_options()
            # Set Solver Options
            xfoil_solver_parameters.max_iter = 1000

            xfoil_solver_parameters.Ncrit = Ncrit
            xfoil_solver_parameters.xtr = (0.1, 1.0)
            xfoil_solver_parameters.print = False
            # xfoil.print_solver_options()

            # RUN and SAVE
            xfoil.define_analysis(xfoil_options, xfoil_solver_parameters)
            xfoil.execute(parallel=True)

            try:
                # Get polar
                polar = DB.foils_db.get_polars(airfoil.name, "Xfoil")

                airfoil_folder = os.path.join("Data/images/")
                polar.save_polar_plot_img(airfoil_folder, 'xfoil')
            except Exception as e:
                print(f"Error saving polar plot. Got: {e}")

            xfoil_etime: float = time.time()
            print(f"XFoil completed in {xfoil_etime - xfoil_stime} seconds")

        # OpenFoam
        if calcOpenFoam:
            of_stime: float = time.time()
            for reyn in reynolds:
                print(f"Running OpenFoam for Re={reyn}")
                from ICARUS.Computation.Solvers.OpenFoam.open_foam import OpenFoam

                open_foam: Solver = OpenFoam()

                # Import Analysis
                analysis = open_foam.get_analyses_names()[0]  # Run
                open_foam.select_analysis(analysis)

                # Get Options
                of_options: Struct = open_foam.get_analysis_options()
                of_solver_parameters: Struct = open_foam.get_solver_parameters()

                # Set Options
                of_options.airfoil = airfoil
                of_options.angles = angles
                of_options.reynolds = reyn
                of_options.mach = MACH
                open_foam.print_analysis_options()

                # Set Solver Options
                of_solver_parameters.mesh_type = MeshType.structAirfoilMesher
                of_solver_parameters.max_iterations = 100
                of_solver_parameters.silent = False
                # xfoil.print_solver_options()

                # RUN
                open_foam.define_analysis(of_options, of_solver_parameters)
                open_foam.execute()
            of_etime: float = time.time()
            print(f"OpenFoam completed in {of_etime - of_stime} seconds")

        airfoil_etime: float = time.time()
        print(
            f"Airfoil {airfoil.name} completed in {airfoil_etime - airfoil_stime} seconds",
        )

    #   ############################### END LOOP ##############################################

    end_time = time.time()
    print(f"Total time: {end_time - start_time}")
    print("########################################################################")
    print("Program Terminated")
    print("########################################################################")


if __name__ == "__main__":
    # # parse command line options
    # # Options are -n for number of processors
    # from ICARUS import CPU_TO_USE

    # from optparse import OptionParser
    # parser = OptionParser()
    # parser.add_option("-n", "--num_proc", type="int", dest="num_proc", default=CPU_TO_USE,
    #                   help="Number of processors to use")
    # (options, args) = parser.parse_args()
    # num_proc = options.num_proc

    # # if num proc is specified, set it
    # if num_proc > 0:
    #     CPU_TO_USE = num_proc

    main()

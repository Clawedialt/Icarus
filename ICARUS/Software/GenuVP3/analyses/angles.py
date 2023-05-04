import os

from ICARUS.Database import BASEGNVP3 as GENUBASE
from ICARUS.Database.db import DB
from ICARUS.Database.utils import ang2case
from ICARUS.Software.GenuVP3.filesInterface import runGNVPcase
from ICARUS.Software.GenuVP3.postProcess.forces import (forces2polars,
                                                        rotateForces)
from ICARUS.Software.GenuVP3.utils import airMov, makeSurfaceDict, setParams


def GNVPangleCase(plane, db, solver2D, maxiter, timestep,
                  Uinf, angle, environment, movements,
                  bodies, solver_options):
    
    HOMEDIR = db.HOMEDIR
    PLANEDIR = os.path.join(db.vehiclesDB.DATADIR, plane.CASEDIR)
    airfoils = plane.airfoils
    foilsDB = db.foilsDB

    print(f"Running Angles {angle}")
    folder = ang2case(angle)
    CASEDIR = os.path.join(PLANEDIR,folder)
    os.makedirs(CASEDIR,exist_ok=True)

    params = setParams(bodies, plane, maxiter,timestep,
                        Uinf, angle, environment,
                        solver_options)
    runGNVPcase(CASEDIR, HOMEDIR, GENUBASE, movements,
                bodies, params, airfoils, foilsDB.Data,
                solver2D)

    return f"Angle {angle} Done"


def runGNVPangles(plane, db, solver2D, maxiter, timestep,
                  Uinf, angles, environment, solver_options):

    movements = airMov(plane.surfaces, plane.CG,
                       plane.orientation, plane.disturbances)
    bodies = []
    if solver_options['Split_Symmetric_Bodies']:
        surfaces = plane.get_seperate_surfaces()
    else:
        surfaces = plane.surfaces
        
    for i, surface in enumerate(surfaces):
        bodies.append(makeSurfaceDict(surface, i))

    print("Running Angles in Sequential Mode")
    for angle in angles:
        msg = GNVPangleCase(plane, db, solver2D, maxiter, timestep,
                            Uinf, angle, environment, movements, bodies,
                            solver_options)
        print(msg)


def runGNVPanglesParallel(plane, db, solver2D, maxiter, timestep, Uinf, angles, environment,
                          solver_options):

    movements = airMov(plane.surfaces, plane.CG,
                       plane.orientation, plane.disturbances)
    bodies = []
    
    if solver_options['Split_Symmetric_Bodies']:
        surfaces = plane.get_seperate_surfaces()
    else:
        surfaces = plane.surfaces
    for i, surface in enumerate(surfaces):
        bodies.append(makeSurfaceDict(surface, i))

    from multiprocessing import Pool
    print("Running Angles in Parallel Mode")
    with Pool(12) as pool:
        args_list = [(plane, db, solver2D, maxiter, timestep,
                      Uinf, angle, environment, movements, bodies, 
                      solver_options) for angle in angles]
        res = pool.starmap(GNVPangleCase, args_list)

        for msg in res:
            print(msg)

def processGNVPangles(plane, db: DB):
    HOMEDIR = db.HOMEDIR
    CASEDIR = os.path.join(db.vehiclesDB.DATADIR, plane.CASEDIR)    
    forces = forces2polars(CASEDIR, HOMEDIR)
    # rotatedforces = rotateForces(forces, forces["AoA"])
    return forces #, rotatedforces
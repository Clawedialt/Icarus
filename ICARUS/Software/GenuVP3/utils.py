import numpy as np


def airMov(surfaces, CG, orientation, disturbances):
    movement = []
    for surface in surfaces:
        sequence = []
        for name, axis in [["pitch", 2], ["roll", 1], ["yaw", 3]]:
            Rotation = {
                "type": 1,
                "axis": axis,
                "t1": -0.1,
                "t2": 0.0,
                "a1": orientation[axis - 1],
                "a2": orientation[axis - 1],
            }
            Translation = {
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


def setParams(
    bodies,
    plane,
    maxiter,
    timestep,
    Uinf,
    angle,
    environment,
    solver_options,
):
    nBodies = len(bodies)
    nAirfoils = len(plane.airfoils)
    angle = angle * np.pi / 180
    dens = environment.AirDensity
    visc = environment.AirDynamicViscosity

    airVelocity = [Uinf * np.cos(angle), 0.0, Uinf * np.sin(angle)]
    params = {
        "nBods": nBodies,
        "nBlades": nAirfoils,
        "maxiter": maxiter,
        "timestep": timestep,
        "Uinf": airVelocity,
        "rho": dens,
        "visc": visc,
        "Split_Symmetric_Bodies": solver_options["Split_Symmetric_Bodies"],
        "Use_Grid": solver_options["Use_Grid"],
        ## LOW LEVEL OPTIONS
        "NMETH": solver_options["Integration_Scheme"],
        "NEMTIP": solver_options["Tip_Emmision"],
        "NTIMET": solver_options["Tip_Emmision_Begins"],
        "NEMSLE": solver_options["Leading_Edge_Separation"],
        "NTIMEL": solver_options["Leading_Edge_Separation_Begins"],
        "RELAXS": solver_options["Relaxation_Factor"],
        "EPSDS": solver_options["Pot_Convergence_Tolerence"],
        "NLEVELT": solver_options["Movement_Levels"],
        "NNEVP0": solver_options["Vortex_Particle_Count"],
        "RELAXU": solver_options["Vortex_Particle_Relaxation"],
        "PARVEC": solver_options["Minimum_Width_Parameter"],
        "NEMIS": solver_options["NEMIS"],
        "EPSFB": solver_options["Bound_Vorticity_Cutoff"],
        "EPSFW": solver_options["Wake_Vorticity_Cutoff"],
        "EPSSR": solver_options["Cutoff_Length_Sources"],
        "EPSDI": solver_options["Cutoff_Length_Sources2"],
        "EPSVR": solver_options["Vortex_Cutoff_Length_f"],
        "EPSO": solver_options["Vortex_Cutoff_Length_i"],
        "EPSINT": solver_options["EPSINT"],
        "COEF": solver_options["Particle_Dissipation_Factor"],
        "RMETM": solver_options["Upper_Deformation_Rate"],
        "IDEFW": solver_options["Wake_Deformation_Parameter"],
        "REFLEN": solver_options["REFLEN"],
        "IDIVVRP": solver_options["Particle_Subdivision_Parameter"],
        "FLENSC": solver_options["Subdivision_Length_Scale"],
        "NREWAK": solver_options["Wake_Particle_Merging_Parameter"],
        "NMER": solver_options["Particle_Merging_Parameter"],
        "XREWAK": solver_options["Merging_Starting_Distance"],
        "RADMER": solver_options["Merging_Radius"],
        "Elasticity_Solver": solver_options["Wake_Vorticity_Cutoff"],
    }
    return params


def makeSurfaceDict(surf, idx):
    if surf.is_symmetric:
        N = 2 * surf.N - 1
        M = surf.M
    else:
        N = surf.N
        M = surf.M

    s = {
        "NB": idx,
        "NACA": surf.airfoil.name,
        "name": surf.name,
        "bld": f"{surf.name}.bld",
        "cld": f"{surf.airfoil.name}.cld",
        "NNB": M,
        "NCWB": N,
        "x_0": surf.origin[0],
        "y_0": surf.origin[1],
        "z_0": surf.origin[2],
        "pitch": surf.orientation[0],
        "cone": surf.orientation[1],
        "wngang": surf.orientation[2],
        "x_end": surf.origin[0] + surf._offset_dist[-1],
        "y_end": surf.origin[1] + surf.span,
        "z_end": surf.origin[2] + surf._dihedral_dist[-1],
        "Root_chord": surf.chord[0],
        "Tip_chord": surf.chord[-1],
        "Offset": surf._offset_dist[-1],
        "Grid": surf.getGrid(),
    }
    return s


def distrubance2movement(disturbance):
    if disturbance.type == "Derivative":
        t1 = -1
        t2 = 0
        a1 = 0
        a2 = disturbance.amplitude
        distType = 8
    elif disturbance.type == "Value":
        t1 = -1
        t2 = 0.0
        a1 = disturbance.amplitude
        a2 = disturbance.amplitude
        distType = 1

    empty = {
        "type": 1,
        "axis": disturbance.axis,
        "t1": -1,
        "t2": 0,
        "a1": 0,
        "a2": 0,
    }

    dist = {
        "type": distType,
        "axis": disturbance.axis,
        "t1": t1,
        "t2": t2,
        "a1": a1,
        "a2": a2,
    }

    if disturbance.isRotational:
        Rotation = dist
        Translation = empty
    else:
        Rotation = empty
        Translation = dist

    return Movement(disturbance.name, Rotation, Translation)


class Movement:
    def __init__(self, name, Rotation, Translation):
        self.name = name
        self.Rtype = Rotation["type"]

        self.Raxis = Rotation["axis"]

        self.Rt1 = Rotation["t1"]
        self.Rt2 = Rotation["t2"]

        self.Ra1 = Rotation["a1"]
        self.Ra2 = Rotation["a2"]

        self.Ttype = Translation["type"]

        self.Taxis = Translation["axis"]

        self.Tt1 = Translation["t1"]
        self.Tt2 = Translation["t2"]

        self.Ta1 = Translation["a1"]
        self.Ta2 = Translation["a2"]

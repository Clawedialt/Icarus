import os

import jsonpickle
import jsonpickle.ext.pandas as jsonpickle_pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ICARUS.Database import DB3D
from ICARUS.Flight_Dynamics.disturbances import Disturbance
from ICARUS.Vehicle.wing import Wing

jsonpickle_pd.register_handlers()


class Airplane:
    def __init__(
        self,
        name: str,
        surfaces: list[Wing],
        disturbances: list[Disturbance] | None = None,
        orientation=None,
    ) -> None:

        self.name = name
        self.CASEDIR = name
        self.surfaces: list[Wing] = surfaces
        self.masses = []

        if disturbances is None:
            self.disturbances = []
        else:
            self.disturbances = disturbances

        if orientation is None:
            self.orientation = [0.0, 0.0, 0.0]
        else:
            self.orientation = orientation

        gotWing = False
        for surface in surfaces:
            if surface.name == "wing":
                self.main_wing = surface
                self.S = surface.S
                self.mean_aerodynamic_chord = surface.mean_aerodynamic_chord
                self.aspect_ratio = surface.aspect_ratio
                self.span = surface.span
                gotWing = True

        if not gotWing:
            self.main_wing = surfaces[0]
            self.S = surfaces[0].S
            self.mean_aerodynamic_chord = surfaces[0].mean_aerodynamic_chord
            self.aspect_ratio = surfaces[0].aspect_ratio
            self.span = surfaces[0].span

        self.airfoils = self.get_all_airfoils()
        self.bodies = []
        self.masses = []
        self.Inertial_moments = []

        self.M = 0
        for surface in self.surfaces:
            mass = (surface.mass, surface.CG)
            mom = surface.inertia

            self.M += surface.mass
            self.Inertial_moments.append(mom)
            self.masses.append(mass)

        self.CG = self.findCG()
        self.total_inertia = self.findInertia(self.CG)

    def get_seperate_surfaces(self) -> list[Wing]:
        surfaces: list[Wing] = []
        for i, surface in enumerate(self.surfaces):
            if surface.is_symmetric:
                l, r = surface.split_symmetric_wing()
                surfaces.append(l)
                surfaces.append(r)
        return surfaces

    def addMasses(self, masses):
        for mass in masses:
            self.masses.append(mass)
        self.CG = self.findCG()
        self.total_inertia = self.findInertia(self.CG)

    def findCG(self):
        x_cm = 0
        y_cm = 0
        z_cm = 0
        self.M = 0
        for m, r in self.masses:
            self.M += m
            x_cm += m * r[0]
            y_cm += m * r[1]
            z_cm += m * r[2]
        return np.array((x_cm, y_cm, z_cm), dtype=float) / self.M

    def findInertia(self, point):
        I_xx = 0
        I_yy = 0
        I_zz = 0
        I_xz = 0
        I_xy = 0
        I_yz = 0

        for inertia in self.Inertial_moments:
            I_xx += inertia[0]
            I_yy += inertia[1]
            I_zz += inertia[2]
            I_xz += inertia[3]
            I_xy += inertia[4]
            I_yz += inertia[5]

        for m, r_bod in self.masses:
            r = point - r_bod
            I_xx += m * (r[1] ** 2 + r[2] ** 2)
            I_yy += m * (r[0] ** 2 + r[2] ** 2)
            I_zz += m * (r[0] ** 2 + r[1] ** 2)
            I_xz += m * (r[0] * r[2])
            I_xy += m * (r[0] * r[1])
            I_yz += m * (r[1] * r[2])

        return np.array((I_xx, I_yy, I_zz, I_xz, I_xy, I_yz))

    def get_all_airfoils(self) -> list[str]:
        airfoils: list[str] = []
        for surface in self.surfaces:
            if f"NACA{surface.airfoil.name}" not in airfoils:
                airfoils.append(f"NACA{surface.airfoil.name}")
        return airfoils

    def visAirplane(self, prev_fig=None, prev_ax=None, movement=None):
        if prev_fig is None:
            fig: Figure = plt.figure()
            ax = fig.add_subplot(projection="3d")
            ax.set_title(self.name)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            ax.view_init(30, 150)
            ax.axis("scaled")
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.set_zlim(-1, 1)
        else:
            fig = prev_fig
            ax = prev_ax

        if movement is None:
            mov = np.zeros(3)
        else:
            mov = movement

        for surface in self.surfaces:
            surface.plot_wing(fig, ax, mov)
        # Add plot for masses
        for m, r in self.masses:
            ax.scatter(  # type: ignore
                r[0] + mov[0],
                r[1] + mov[1],
                r[2] + mov[2],
                marker="o",
                s=m * 50.0,
                color="r",
            )
        ax.scatter(  # type: ignore
            self.CG[0] + mov[0],
            self.CG[1] + mov[1],
            self.CG[2] + mov[2],
            marker="o",
            s=50.0,
            color="b",
        )

    def defineSim(self, u, dens):
        self.u_freestream: float = u
        self.dens: float = dens
        self.dynamic_pressure: float = 0.5 * dens * u**2

    def toJSON(self) -> str:
        encoded = jsonpickle.encode(self)
        return encoded

    def save(self):
        fname = os.path.join(DB3D, self.CASEDIR, f"{self.name}.json")
        with open(fname, "w") as f:
            f.write(self.toJSON())

    # def __str__(self):
    #     str = f"Plane Object for {self.name}\n"
    #     str += f"Surfaces:\n"
    #     for i,surfaces in enumerate(self.surfaces):
    #         str += f"\t{surfaces.name} NB={i} with Area: {surfaces.S}, Inertia: {surfaces.I}, Mass: {surfaces.M}\n"
    #     return str

    def __str__(self):
        str = f"Plane Object: {self.name}"
        return str

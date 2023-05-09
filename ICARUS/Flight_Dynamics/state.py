from pandas import DataFrame

from .disturbances import Disturbance as dst
from .dyn_plane import StabilityDerivativesDS
from .pertrubations import lateralPerturb
from .pertrubations import longitudalPerturb
from .Stability.lateralFD import lateralStability
from .Stability.longitudalFD import longitudalStability
from .trim import trim_state
from ICARUS.Core.struct import Struct
from ICARUS.Enviroment.definition import Environment
from ICARUS.Software.GenuVP3.postProcess.forces import rotateForces
from ICARUS.Vehicle.plane import Airplane


class State:
    """Class for the state of a vehicle."""

    def __init__(self, name: str, pln: Airplane, forces, env: Environment) -> None:
        self.vehicle: Airplane = pln
        self.S: float = pln.S
        self.mean_aerodynamic_chord: float = pln.mean_aerodynamic_chord

        self.name: str = name
        self.polars: DataFrame = self.formatPolars(forces)

        self.trim: dict[str, float] = trim_state(self)
        self.dynamic_pressure: float = (
            0.5 * env.AirKinematicViscosity * self.trim["U"] ** 2
        )
        self.disturbances: list[dst] = []
        self.sensitivity = Struct()
        self.sensResults = Struct()

    def formatPolars(self, forces) -> DataFrame:
        forces_rotated: DataFrame = rotateForces(forces, forces["AoA"])
        return self.makeAeroCoeffs(forces_rotated)

    def makeAeroCoeffs(self, Forces) -> DataFrame:
        Data: DataFrame = DataFrame()

        Data["CL"] = Forces["Fz"] / (self.dynamic_pressure * self.S)
        Data["CD"] = Forces["Fx"] / (self.dynamic_pressure * self.S)
        Data["Cm"] = Forces["M"] / (
            self.dynamic_pressure * self.S * self.mean_aerodynamic_chord
        )
        Data["Cn"] = Forces["N"] / (
            self.dynamic_pressure * self.S * self.mean_aerodynamic_chord
        )
        Data["Cl"] = Forces["L"] / (
            self.dynamic_pressure * self.S * self.mean_aerodynamic_chord
        )
        Data["AoA"] = Forces["AoA"]
        return Data

    def all_Pertrubations(self, scheme: str, epsilon=None) -> None:
        """Function to add a perturbations to the airplane for
        dynamic analysis
        Inputs:
        - scheme: "Central", "Forward", "Backward"
        - epsilon: Disturbance Magnitudes
        """
        self.scheme: str = scheme
        self.epsilons: dict[str, float] = {}

        self.disturbances = [
            *longitudalPerturb(self, scheme, epsilon),
            *lateralPerturb(self, scheme, epsilon),
        ]
        self.disturbances.append(dst(None, 0))

    def sensitivityAnalysis(self, var, space):
        self.sensitivity[var] = []
        for e in space:
            self.sensitivity[var].append(dst(var, e))

    def get_pertrub(self):
        for disturbance in self.disturbances:
            print(disturbance)

    def setPertResults(self, makePolFun, args, kwargs={}):
        petrubdf = makePolFun(*args, **kwargs)
        self.pertubResults = petrubdf

    def stabilityFD(self, scheme="Central"):
        self.scheme = scheme
        X, Z, M = longitudalStability(self, "2D")
        Y, L, N = lateralStability(self, "Potential")
        self.SBderivativesDS = StabilityDerivativesDS(X, Y, Z, L, M, N)

    def __str__(self):
        str = f"Dynamic AirPlane {self.name}"
        # str += f"\nTrimmed at: {self.trim['U']} m/s, {self.trim['AoA']} deg\n"
        # str += f"Surfaces:\n"
        # for surfaces in self.surfaces:
        #     str += f"\n\t{surfaces.name} with Area: {surfaces.S}, Inertia: {surfaces.I}, Mass: {surfaces.M}\n"
        return str

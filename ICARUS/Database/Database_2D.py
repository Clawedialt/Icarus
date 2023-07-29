import os
import shutil
from typing import Any

import numpy as np
import pandas as pd
from numpy import dtype
from numpy import floating
from numpy import ndarray

from . import APPHOME
from . import DB2D
from ICARUS.Airfoils.airfoilD import AirfoilD
from ICARUS.Core.struct import Struct


class Database_2D:
    """
    Database class to store 2d simulation objects (airfoils), analyses and results (polars).
    """

    def __init__(self) -> None:
        """
        Initialize the Database_2D class.
        """
        self.HOMEDIR: str = APPHOME
        self.DATADIR: str = DB2D
        if not os.path.isdir(self.DATADIR):
            os.makedirs(self.DATADIR)

        self.data: Struct = Struct()

    def load_data(self) -> None:
        """
        Scans the filesystem and load all the data.
        """
        self.scan()
        self.airfoils: Struct = self.set_available_airfoils()

    def scan(self) -> None:
        """
        Scans the filesystem and loads data if not already loaded.
        """
        # Accessing Database Directory
        try:
            os.chdir(DB2D)
        except FileNotFoundError:
            print(f"Database not found! Initializing Database at {DB2D}")
            os.makedirs(DB2D, exist_ok=True)
        # Get Folders
        folders: list[str] = next(os.walk("."))[1]
        data = Struct()
        for airfoil in folders:
            os.chdir(airfoil)
            data[airfoil] = self.scan_reynold_subdirs()
            os.chdir(DB2D)

        for airfoil in data.keys():
            if airfoil not in self.data.keys():
                self.data[airfoil] = Struct()

            for j in data[airfoil].keys():
                for k in data[airfoil][j].keys():
                    if k not in self.data[airfoil].keys():
                        self.data[airfoil][k] = Struct()
                    self.data[airfoil][k][j] = data[airfoil][j][k]
        os.chdir(self.HOMEDIR)

    def scan_reynold_subdirs(self) -> Struct:
        """
        Scans the reynolds subdirectories and loads the data.

        Returns:
            Struct: A struct containing the polars for all reynolds.
        """
        airfoil_data = Struct()
        folders: list[str] = next(os.walk("."))[1]  # folder = reynolds subdir
        for folder in folders:
            os.chdir(folder)
            airfoil_data[folder[9:]] = self.scan_different_solver()
            os.chdir("..")
        return airfoil_data

    def scan_different_solver(self) -> Struct:
        """
        Scans the different solver files and loads the data.

        Raises:
            ValueError: If it encounters a solver not recognized.

        Returns:
            Struct: Struct containing the polars for all solvers.
        """
        current_reynolds_data = Struct()
        files: list[str] = next(os.walk("."))[2]
        for file in files:
            if file.startswith("clcd"):
                solver: str = file[5:]
                if solver == "f2w":
                    name = "Foil2Wake"
                elif solver == "of":
                    name = "OpenFoam"
                elif solver == "xfoil":
                    name = "Xfoil"
                else:
                    raise ValueError("Solver not recognized!")
                try:
                    current_reynolds_data[name] = pd.read_csv(file, dtype=float)
                except ValueError:
                    current_reynolds_data[name] = pd.read_csv(
                        file,
                        delimiter="\t",
                        dtype=float,
                    )
        return current_reynolds_data

    def set_available_airfoils(self) -> Struct:
        airfoils = Struct()
        for airf in list(self.data.keys()):
            airfoils[airf] = AirfoilD.naca(airf[4:], n_points=200)

        return airfoils

    def get_airfoil_solvers(self, airfoil_name: str) -> list[str] | None:
        """
        Get the solvers for a given airfoil.

        Args:
            airfoil_name (str): Airfoil Name

        Returns:
            list[str] | None: The solver names or None if the airfoil doesn't exist.
        """
        try:
            return list(self.data[airfoil_name].keys())
        except KeyError:
            print("Airfoil Doesn't exist! You should compute it first!")
            return None

    def get_airfoil_reynolds(self, airfoil_name: str) -> list[str] | None:
        """
        Returns the reynolds numbers computed for a given airfoil.

        Args:
            airfoil_name (str): Airfoil Name

        Returns:
            list[str] | None: List of reynolds numbers computed or None if the airfoil doesn't exist.
        """
        try:
            reynolds: list[str] = []
            for solver in self.data[airfoil_name].keys():
                for reyn in self.data[airfoil_name][solver].keys():
                    reynolds.append(reyn)
            return reynolds
        except KeyError:
            print("Airfoil Doesn't exist! You should compute it first!")
            return None

    @staticmethod
    def angle_to_dir(angle: float) -> str:
        """
        Converts an angle to a directory name.

        Args:
            angle (float): Angle

        Returns:
            str: Directory name
        """
        if angle >= 0:
            folder: str = str(angle)[::-1].zfill(7)[::-1]
        else:
            folder = "m" + str(angle)[::-1].strip("-").zfill(6)[::-1]
        return folder

    def generate_airfoil_directories(
        self,
        airfoil: AirfoilD,
        reynolds: float,
        angles: list[float] | ndarray[Any, dtype[floating[Any]]],
    ) -> tuple[str, str, str, list[str]]:
        AFDIR = os.path.join(
            self.DATADIR,
            f"NACA{airfoil.name}",
        )
        os.makedirs(AFDIR, exist_ok=True)
        exists = False
        for i in os.listdir():
            if i.startswith("naca"):
                exists = True
        if not exists:
            airfoil.save(AFDIR)

        reynolds_str: str = np.format_float_scientific(
            reynolds,
            sign=False,
            precision=3,
        )

        REYNDIR: str = os.path.join(
            AFDIR,
            f"Reynolds_{reynolds_str.replace('+', '')}",
        )
        os.makedirs(REYNDIR, exist_ok=True)
        airfile = os.path.join(
            AFDIR,
            airfoil.file_name,
        )
        shutil.copy(airfile, REYNDIR)

        ANGLEDIRS: list[str] = []
        for angle in angles:
            folder = self.angle_to_dir(angle)
            ANGLEDIRS.append(os.path.join(REYNDIR, folder))

        return self.HOMEDIR, AFDIR, REYNDIR, ANGLEDIRS

    def __str__(self) -> str:
        return "Foil Database"

    # def __enter__(self) -> None:
    #     """
    #     TODO: Implement this method.
    #     """
    #     pass

    # def __exit__(self) -> None:
    #     """
    #     TODO: Implement this method.
    #     """
    #     pass

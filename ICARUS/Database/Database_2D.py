import os
import re
import shutil
from time import sleep
from typing import Any

import numpy as np
import pandas as pd
from numpy import dtype
from numpy import floating
from numpy import ndarray
from pandas import DataFrame

from . import APPHOME
from . import DB2D
from . import XFLRDB
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

    def set_available_airfoils(self, verbose: bool = False) -> Struct:
        airfoils = Struct()
        for airf in list(self.data.keys()):
            try:
                airfoils[airf] = AirfoilD.naca(airf[4:], n_points=200)
                if verbose:
                    print(f"Loaded Airfoil {airf} from NACA Digits")
            except:
                # try to load the airfoil from the DB2D
                try:
                    filename = os.path.join(DB2D, airf, airf.replace("NACA", "naca"))
                    airfoils[airf] = AirfoilD.load_from_file(filename)
                    if verbose:
                        print(f"Loaded Airfoil {airf} from DB2D")
                except:
                    # Try to load the airfoil from the XFLR5DB
                    #! TODO DEPRECATE THIS IT IS STUPID AIRFOILS SHOULD BE MORE ROBUST

                    # list the folders in the XFLR5DB
                    folders: list[str] = os.walk(XFLRDB).__next__()[1]
                    flag = False
                    name = ""
                    for folder in folders:
                        pattern = r"\([^)]*\)|[^0-9a-zA-Z]+"
                        cleaned_string: str = re.sub(pattern, " ", folder)
                        # Split the cleaned string into numeric and text parts
                        foil: str = "".join(filter(str.isdigit, cleaned_string))
                        text_part: str = "".join(filter(str.isalpha, cleaned_string))
                        if text_part.find("flap") != -1:
                            name: str = f"{foil + 'fl'}"
                        else:
                            name = foil

                        if len(airf) == 4 or len(airf) == 5:
                            name = "NACA" + name

                        if name == airf:
                            flag = True
                            name = folder

                    if flag:
                        # list the files in the airfoil folder
                        flap_files: list[str] = os.listdir(os.path.join(XFLRDB, name))
                        # check if the airfoil is in the flap folder
                        if name + ".dat" in flap_files:
                            # load the airfoil from the flap folder
                            filename = os.path.join(XFLRDB, name, name + ".dat")
                            airfoils[airf] = AirfoilD.load_from_file(filename)
                            if verbose:
                                print(f"Loaded Airfoil {airf} from XFLR5DB")
                    else:
                        raise FileNotFoundError(f"Couldnt Find Airfoil {airf} in DB2D or XFLR5DB")
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

    def generate_airfoil_directories(
        self,
        airfoil: AirfoilD,
        reynolds: float,
        angles: list[float] | ndarray[Any, dtype[floating[Any]]],
    ) -> tuple[str, str, str, list[str]]:
        AFDIR: str = os.path.join(
            self.DATADIR,
            f"NACA{airfoil.name}",
        )
        os.makedirs(AFDIR, exist_ok=True)
        exists = False
        for i in os.listdir():
            if i.startswith("naca"):
                exists = True
        if not exists:
            airfoil.save_selig_te(AFDIR)
            sleep(0.1)

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

    # STATIC METHODS
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

    @staticmethod
    def dir_to_angle(folder: str) -> float:
        """
        Converts a directory name to an angle.

        Args:
            folder (str): Directory name

        Returns:
            float: Angle
        """
        if folder.startswith("m"):
            angle = -float(folder[1:])
        else:
            angle = float(folder)
        return angle

    @staticmethod
    def get_reynolds_from_dir(folder: str) -> float:
        """
        Gets the reynolds number from a directory name.

        Args:
            folder (str): Directory name

        Returns:
            float: Reynolds number
        """
        return float(folder[10:].replace("_", "e"))

    @staticmethod
    def get_dir_from_reynolds(reynolds: float) -> str:
        """
        Gets the directory name from a reynolds number.

        Args:
            reynolds (float): Reynolds number

        Returns:
            str: Directory name
        """
        return f"Reynolds_{reynolds}"

    @staticmethod
    def fill_polar_table(df: DataFrame) -> DataFrame:
        """Fill Nan Values of Panda Dataframe Row by Row
        substituting first backward and then forward
        #! TODO: DEPRECATE THIS METHOD IN FAVOR OF POLAR CLASS

        Args:
            df (pandas.DataFrame): Dataframe with NaN values
        """
        CLs: list[str] = []
        CDs: list[str] = []
        CMs: list[str] = []
        for item in list(df.keys()):
            if item.startswith("CL"):
                CLs.append(item)
            if item.startswith("CD"):
                CDs.append(item)
            if item.startswith("Cm") or item.startswith("CM"):
                CMs.append(item)
        for colums in [CLs, CDs, CMs]:
            df[colums] = df[colums].interpolate(
                method="linear",
                limit_direction="backward",
                axis=1,
            )
            df[colums] = df[colums].interpolate(
                method="linear",
                limit_direction="forward",
                axis=1,
            )
        df.dropna(axis=0, subset=df.columns[1:], how="all", inplace=True)
        return df

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

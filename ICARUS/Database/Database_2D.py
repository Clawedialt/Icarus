from . import DB2D
import os
import pandas as pd
import numpy as np
from ICARUS.Airfoils import airfoil as af


class Database_2D():
    def __init__(self, HOMEDIR):
        self.HOMEDIR = HOMEDIR
        self.Data = {}
        self.scan()
        self.airfoils = self.getAirfoils()

    def scan(self):
        os.chdir(DB2D)
        folders = next(os.walk('.'))[1]
        Data = {}
        for folder in folders:
            os.chdir(folder)
            Data[folder] = self.scanReynolds()
            os.chdir(DB2D)

        self.Data = {}
        for i in Data.keys():
            if i not in self.Data.keys():
                self.Data[i] = {}
            for j in Data[i].keys():
                for k in Data[i][j].keys():
                    if k not in self.Data[i].keys():
                        self.Data[i][k] = {}
                    self.Data[i][k][j] = Data[i][j][k]
        os.chdir(self.HOMEDIR)

    def scanReynolds(self):
        airfoilDict = {}
        folders = next(os.walk('.'))[1]
        for folder in folders:
            os.chdir(folder)
            airfoilDict[folder[9:]] = self.scanSolvers()
            os.chdir('../')
        return airfoilDict

    def scanSolvers(self):
        reynDict = {}
        files = next(os.walk('.'))[2]
        for file in files:
            if file.startswith('clcd'):
                solver = file[5:]
                if solver == "f2w":
                    name = "Foil2Wake"
                elif solver == 'of':
                    name = "OpenFoam"
                elif solver == 'xfoil':
                    name = "Xfoil"
                reynDict[name] = pd.read_csv(file)
        return reynDict

    def getAirfoils(self):
        airfoils = {}
        for airf in list(self.Data.keys()):
            airfoils[airf] = af.AirfoilData.NACA(
                airf[4:], n_points=200)

        return airfoils

    def getSolver(self, airfoil):
        try:
            return list(self.Data[str(airfoil)].keys())
        except KeyError:
            print("Airfoil Doesn't exist! You should compute it first!")

    def getReynolds(self, airfoil):
        try:
            reynolds = []
            for solver in self.Data[str(airfoil)].keys():
                for reyn in self.Data[str(airfoil)][solver].keys():
                    reynolds.append(reyn)
            return reynolds
        except KeyError:
            print("Airfoil Doesn't exist! You should compute it first!")

    def addXFLRPolars(self, XFLRdir):
        os.chdir(XFLRdir)
        files = next(os.walk('.'))[1]
        for airfoil in files:
            if airfoil.startswith("NACA"):
                os.chdir(airfoil)
                dat = next(os.walk('.'))[2]
                for polar in dat:
                    if polar.startswith("NACA"):
                        foo = polar[4:].split("_")
                        reyn = float(foo[2][2:]) * 1e6
                        dat = pd.read_csv(polar, sep='  ', header=None,
                                          skiprows=11, engine='python')
                        dat.columns = xfoilcols
                        dat = dat.drop(["CDp",
                                       "Top Xtr",
                                        "Bot Xtr",
                                        "Cpmin",
                                        "Chinge",
                                        "_",
                                        "_",
                                        "XCp"
                                        ], axis=1)
                        if "XFLR" not in self.Data[airfoil].keys():
                            self.Data[airfoil]["XFLR"] = {}
                        reyn = np.format_float_scientific(
                            reyn, sign=False, precision=3).replace('+', '')
                        self.Data[airfoil]['XFLR'][reyn] = dat
                os.chdir(XFLRdir)


xfoilcols = [
    "AoA",
    "CL",
    "CD",
    "CDp",
    "Cm",
    "Top Xtr",
    "Bot Xtr",
    "Cpmin",
    "Chinge",
    "_",
    "_",
    "XCp"
]

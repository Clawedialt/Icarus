import numpy as np
from . import DB2D
import os
import pandas as pd


class Database_2D():
    def __init__(self, HOMEDIR):
        self.HOMEDIR = HOMEDIR
        self.Data = {}
        self.scan()

    def scan(self):
        os.chdir(DB2D)
        folders = next(os.walk('.'))[1]
        for folder in folders:
            os.chdir(folder)
            self.Data[folder] = self.scanReynolds()
            os.chdir(DB2D)
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
                elif solver == 'xf':
                    name = "Xfoil"
                reynDict[name] = pd.read_csv(file)
        return reynDict

    def getAirfoils(self):
        return list(self.Data.keys())

    def getReynolds(self, airfoil):
        try:
            return list(self.Data[str(airfoil)].keys())
        except KeyError:
            print("Airfoil Doesn't exist! You should compute it first!")
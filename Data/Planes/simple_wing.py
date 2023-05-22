from typing import Any

import numpy as np
from numpy import dtype
from numpy import floating
from numpy import ndarray

from ICARUS.Core.struct import Struct
from ICARUS.Database import XFLRDB
from ICARUS.Database.Database_2D import Database_2D
from ICARUS.Database.db import DB
from ICARUS.Software.XFLR5.polars import read_polars_2d
from ICARUS.Vehicle.plane import Airplane as Plane
from ICARUS.Vehicle.wing import define_linear_chord
from ICARUS.Vehicle.wing import define_linear_span
from ICARUS.Vehicle.wing import Wing

db: DB = DB()
db.load_data()
db2d: Database_2D = db.foilsDB
read_polars_2d(db2d, XFLRDB)
airfoils: Struct = db2d.set_available_airfoils()

origin: ndarray[Any, dtype[floating[Any]]] = np.array([0.0, 0.0, 0.0], dtype=float)
wing_position: ndarray[Any, dtype[floating[Any]]] = np.array(
    [-0.2, 0.0, 0.0],
    dtype=float,
)
wing_orientation: ndarray[Any, dtype[floating[Any]]] = np.array(
    [0.0, 0.0, 0.0],
    dtype=float,
)

Simplewing = Wing(
    name="bmark",
    airfoil=airfoils["NACA0015"],
    origin=origin + wing_position,
    orientation=wing_orientation,
    is_symmetric=True,
    span=2 * 2.5,
    sweep_offset=0.0,
    dih_angle=0,
    chord_fun=define_linear_chord,
    chord=np.array([0.8, 0.8]),
    span_fun=define_linear_span,
    N=20,
    M=5,
    mass=1,
)
airplane = Plane(Simplewing.name, [Simplewing])
airplane.CG = np.array([0.337, 0, 0])

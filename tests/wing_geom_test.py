import numpy as np

from ICARUS.Core.types import FloatArray
from ICARUS.Vehicle.plane import Airplane


def geom() -> None:
    print("Testing Geometry...")

    from examples.Vehicles.Planes.benchmark_plane import get_bmark_plane

    bmark: Airplane = get_bmark_plane("bmark")

    S = bmark.S
    MAC = bmark.mean_aerodynamic_chord
    AR = bmark.aspect_ratio
    CG = bmark.CG
    INERTIA = bmark.total_inertia

    S_act: tuple[float] = (4.0,)
    MAC_act: tuple[float] = (0.8,)
    AREA_act: tuple[float] = (4.0608,)
    CG_act: FloatArray = np.array([0.337, 0.0, 0.0])
    I_act: FloatArray = np.array(
        [2.077, 0.017, 2.094, 0.0, 0.0, 0.0],
    )

    np.testing.assert_almost_equal(S, S_act, decimal=4)
    np.testing.assert_almost_equal(MAC, MAC_act, decimal=4)
    # np.testing.assert_almost_equal(AREA, AREA_act, decimal=4)
    np.testing.assert_almost_equal(CG, CG_act, decimal=3)
    np.testing.assert_almost_equal(INERTIA, I_act, decimal=3)

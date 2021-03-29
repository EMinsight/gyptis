#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# License: MIT


from pprint import pprint

import pytest
from scipy.spatial.transform import Rotation

from gyptis import Grating, Layered
from gyptis.geometry import *
from gyptis.grating2d import Grating2D, Layered2D, OrderedDict
from gyptis.helpers import list_time
from gyptis.plot import *
from gyptis.source import *

pytest_params = [("TE", 1), ("TM", 1), ("TE", 2), ("TM", 2)]

tol_balance = 1e-2
pmesh = 10


@pytest.mark.parametrize("polarization,degree", pytest_params)
def test_grating2d(polarization, degree):

    wavelength = 1
    lmin = wavelength / pmesh
    period = 0.8
    R = period / 3

    thicknesses = OrderedDict(
        {
            "pml_bottom": wavelength,
            "substrate": wavelength,
            "groove": 3 * R,
            "superstrate": wavelength,
            "pml_top": wavelength,
        }
    )

    rot = Rotation.from_euler("zyx", [10, 0, 0], degrees=True)
    rmat = rot.as_matrix()
    eps_diff = rmat @ np.diag((8 - 0.1j, 3 - 0.1j, 4 - 0.2j)) @ rmat.T

    mu_groove = rmat @ np.diag((2 - 0.1j, 9 - 0.1j, 3 - 0.2j)) @ rmat.T

    epsilon = dict({"substrate": 2.1, "groove": 1, "superstrate": 1, "diff": eps_diff})
    mu = dict({"substrate": 1.6, "groove": mu_groove, "superstrate": 1, "diff": 1})

    geom = Layered(2, period, thicknesses)

    yc = geom.y_position["groove"] + thicknesses["groove"] / 2
    diff = geom.add_circle(0, yc, 0, R)
    diff, groove = geom.fragment(diff, geom.layers["groove"])
    geom.add_physical(groove, "groove")
    geom.add_physical(diff, "diff")

    [geom.set_size(pml, lmin) for pml in ["pml_bottom", "pml_top"]]
    geom.set_size("groove", lmin)
    geom.set_size("diff", lmin)

    geom.build()

    theta0 = 10

    angle = np.pi / 2 - theta0 * np.pi / 180

    pw = PlaneWave(
        wavelength=wavelength, angle=angle, dim=2, domain=geom.mesh, degree=degree
    )
    s = Grating(geom, epsilon, mu, source=pw, degree=degree, polarization=polarization)

    u = s.solve()
    list_time()

    plt.ion()
    effs = s.diffraction_efficiencies(1, orders=True, subdomain_absorption=True)
    print(effs)

    if degree == 2:
        assert abs(effs["B"] - 1) < tol_balance, "Unsatified energy balance"

    plt.ion()
    # s.plot_geometry(c="k")

    plt.clf()

    s.plot_field(nper=3)
    s.plot_geometry(nper=3, c="k")


@pytest.mark.parametrize("polarization,degree", pytest_params)
def test_grating2dpec(polarization, degree):
    wavelength = 600
    period = 800
    h = 300
    w = 600
    theta0 = 20
    lmin = wavelength / pmesh
    lmin_pec = h / (pmesh * 2)
    thicknesses = OrderedDict(
        {
            "pml_bottom": wavelength,
            "substrate": wavelength,
            "groove": wavelength,
            "superstrate": wavelength,
            "pml_top": wavelength,
        }
    )
    rot = Rotation.from_euler("zyx", [20, 0, 0], degrees=True)
    rmat = rot.as_matrix()
    eps_groove = 1  # rmat @ np.diag((4 - 0.01j, 3 - 0.01j, 2 - 0.02j)) @ rmat.T
    mu_groove = 1  # rmat @ np.diag((2 - 0.01j, 4 - 0.01j, 3 - 0.02j)) @ rmat.T

    epsilon = dict({"substrate": 1.0, "groove": eps_groove, "superstrate": 1})
    mu = dict({"substrate": 1.0, "groove": mu_groove, "superstrate": 1})

    geom = Layered2D(period, thicknesses)

    yc = geom.y_position["groove"] + thicknesses["groove"] / 2
    diff = geom.add_ellipse(0, yc, 0, w / 2, h / 2)
    groove = geom.cut(geom.layers["groove"], diff)

    geom.add_physical(groove, "groove")
    bnds = geom.get_boundaries("groove")
    geom.add_physical(bnds[-1], "hole", dim=1)

    for dom in ["substrate", "superstrate", "pml_bottom", "pml_top", "groove"]:
        geom.set_size(dom, lmin)

    geom.set_size("hole", lmin_pec, dim=1)

    geom.build()

    angle = np.pi / 2 - theta0 * np.pi / 180

    pw = PlaneWave(
        wavelength=wavelength, angle=angle, dim=2, domain=geom.mesh, degree=degree
    )

    boundary_conditions = {"hole": "PEC"}

    s = Grating2D(
        geom,
        epsilon,
        mu,
        source=pw,
        degree=degree,
        polarization=polarization,
        boundary_conditions=boundary_conditions,
    )
    u = s.solve()
    list_time()
    effs = s.diffraction_efficiencies(1, orders=True, subdomain_absorption=True)
    pprint(effs)
    if degree == 2:
        assert abs(effs["B"] - 1) < tol_balance, "Unsatified energy balance"
    # # s.plot_geometry(c="k")
    #

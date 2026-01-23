#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.2
# License: MIT
# See the documentation at gyptis.gitlab.io
"""
2D Anisotropic Grating
=======================

Example of diffraction grating with trapezoidal ridges made from an anisotropic material.
"""


from collections import OrderedDict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

import gyptis as gy

##############################################################################
# We will study this benchmark and compare with results
# given in :cite:p:`PopovGratingBook`.

reference_results = {
    "TM": {
        "0": {
            "T-2": 0,
            "T-1": 0.203133,
            "T0": 0.585235,
            "T1": 0.203138,
            "R-1": 0,
            "R0": 0.008473,
            "R1": 0,
            "total": 0.999978,
        },
        "20": {
            "T-2": 0,
            "T-1": 0.399719,
            "T0": 0.575625,
            "T1": 0.004643,
            "R-1": 0.004412,
            "R0": 0.015630,
            "R1": 0,
            "total": 1.000029,
        },
        "40": {
            "T-2": 0.025047,
            "T-1": 0.420714,
            "T0": 0.493491,
            "T1": 0,
            "R-1": 0.002541,
            "R0": 0.058238,
            "R1": 0,
            "total": 1.000031,
        },
    },
    "TE": {
        "0": {
            "T-2": 0,
            "T-1": 0.322510,
            "T0": 0.538165,
            "T1": 0.124722,
            "R-1": 0,
            "R0": 0.014683,
            "R1": 0,
            "total": 1.000080,
        },
        "20": {
            "T-2": 0,
            "T-1": 0.538727,
            "T0": 0.444403,
            "T1": 0.000369,
            "R-1": 0.005372,
            "R0": 0.011180,
            "R1": 0,
            "total": 1.000051,
        },
        "40": {
            "T-2": 0.012058,
            "T-1": 0.434191,
            "T0": 0.541090,
            "T1": 0,
            "R-1": 0.005032,
            "R0": 0.007686,
            "R1": 0,
            "total": 1.000057,
        },
    },
}


fig, ax = plt.subplots(3, 2, figsize=(3.5, 5.5))


lambda0 = 633
period = 600

width_bottom, width_top = 500, 300
height = 600
eps_sub = 2.25
eps_rod = np.array([[2.592, 0.251, 0], [0.251, 2.592, 0], [0, 0, 2.829]])

pmesh = 10

thicknesses = OrderedDict(
    {
        "pml_bottom": 1 * lambda0,
        "substrate": 2 * lambda0,
        "groove": height * 1.5,
        "superstrate": 2 * lambda0,
        "pml_top": 1 * lambda0,
    }
)

mesh_param = dict(
    {
        "pml_bottom": pmesh * eps_sub**0.5,
        "substrate": pmesh * eps_sub**0.5,
        "groove": pmesh,
        "rod": pmesh * np.max(eps_rod) ** 0.5,
        "superstrate": pmesh,
        "pml_top": pmesh,
    }
)


geom = gy.Layered(2, period, thicknesses)
groove = geom.layers["groove"]
substrate = geom.layers["substrate"]
y0 = geom.y_position["groove"]
P = [geom.add_point(-width_bottom / 2, y0, 0)]
P.append(geom.add_point(width_bottom / 2, y0, 0))
P.append(geom.add_point(width_top / 2, y0 + height, 0))
P.append(geom.add_point(-width_top / 2, y0 + height, 0))
L = [
    geom.add_line(P[0], P[1]),
    geom.add_line(P[1], P[2]),
    geom.add_line(P[2], P[3]),
    geom.add_line(P[3], P[0]),
]
cl = geom.add_curve_loop(L)
rod = geom.add_plane_surface(geom.dimtag(cl, 1)[0])
substrate, groove, rod = geom.fragment([substrate, groove], rod)
geom.add_physical(rod, "rod")
geom.add_physical(groove, "groove")
geom.add_physical(substrate, "substrate")
mesh_size = {d: lambda0 / param for d, param in mesh_param.items()}
geom.set_mesh_size(mesh_size)

geom.build()
all_domains = geom.subdomains["surfaces"]
domains = [k for k in all_domains.keys() if k not in ["pml_bottom", "pml_top"]]

epsilon = {d: 1 for d in domains}
mu = {d: 1 for d in domains}

epsilon["substrate"] = eps_sub
epsilon["rod"] = eps_rod


nper = 8


computed_results = dict(TE=dict(), TM=dict())


angles = [0, 20, 40]


for jangle, angle in enumerate(angles):
    angle_degree = -angle * np.pi / 180

    computed_results["TE"][str(angle)] = {}
    computed_results["TM"][str(angle)] = {}

    pw = gy.PlaneWave(lambda0, angle_degree, dim=2)
    grating_TM = gy.Grating(geom, epsilon, mu, source=pw, polarization="TM", degree=2)
    grating_TM.solve()
    effs_TM = grating_TM.diffraction_efficiencies(2, orders=True)

    ylim = geom.y_position["substrate"], geom.y_position["pml_top"]
    d = grating_TM.period
    vmin_TM, vmax_TM = -1.5, 1.7
    plt.sca(ax[jangle][0])
    per_plots, cb = grating_TM.plot_field(nper=nper)
    cb.remove()
    scatt_lines, layers_lines = grating_TM.plot_geometry(nper=nper, c="k")
    [layers_lines[i].remove() for i in [0, 1, 3, 4]]
    plt.ylim(ylim)
    plt.xlim(-d / 2, nper * d - d / 2)
    plt.axis("off")

    # TE
    grating_TE = gy.Grating(geom, epsilon, mu, source=pw, polarization="TE", degree=2)

    grating_TE.solve()
    effs_TE = grating_TE.diffraction_efficiencies(2, orders=True)

    H = grating_TE.solution["total"]

    vmin_TE, vmax_TE = -2.5, 2.5
    plt.sca(ax[jangle][1])
    per_plots, cb = grating_TE.plot_field(nper=nper)
    cb.remove()
    scatt_lines, layers_lines = grating_TE.plot_geometry(nper=nper, c="k")
    [layers_lines[i].remove() for i in [0, 1, 3, 4]]
    plt.ylim(ylim)
    plt.xlim(-d / 2, nper * d - d / 2)
    plt.axis("off")

    ax[jangle][0].set_title(rf"$\theta = {angle}\degree$")
    ax[jangle][1].set_title(rf"$\theta = {angle}\degree$")


    for m in range(-1,2):
        computed_results["TE"][str(angle)][f"R{m}"] = float(effs_TE["R"][m+2])
        computed_results["TM"][str(angle)][f"R{m}"] = float(effs_TM["R"][m+2])
    

    for m in range(-2,2):
        computed_results["TE"][str(angle)][f"T{m}"] = float(effs_TE["T"][m+2])
        computed_results["TM"][str(angle)][f"T{m}"] = float(effs_TM["T"][m+2])

    computed_results["TE"][str(angle)]["total"] =  effs_TE["B"]
    computed_results["TM"][str(angle)]["total"] =  effs_TM["B"]



divider = make_axes_locatable(ax[0, 0])
cax = divider.new_vertical(size="5%", pad=0.5)
fig.add_axes(cax)
mTM = plt.cm.ScalarMappable(cmap="RdBu")
mTM.set_clim(vmin_TM, vmax_TM)

cbarTM = fig.colorbar(mTM, cax=cax, orientation="horizontal")
cax.set_title(r"${\rm Re}\, E_z$ (TM)")

divider = make_axes_locatable(ax[0, 1])
cax = divider.new_vertical(size="5%", pad=0.5)

mTE = plt.cm.ScalarMappable(cmap="RdBu")
mTE.set_clim(vmin_TE, vmax_TE)
fig.add_axes(cax)
cbarTE = fig.colorbar(mTE, cax=cax, orientation="horizontal")
cax.set_title(r"${\rm Re}\, H_z$ (TE)")

plt.tight_layout()
plt.subplots_adjust(wspace=-0.1, hspace=-0.3)

# Function to display results
def display_results(ref, comp):
    for pol in ref:
        print(f"\n=== Polarization: {pol} ===")
        for angle in ref[pol]:
            print(f"\nAngle: {angle} degrees")
            # Table header
            print("{:<6} {:>12} {:>12} {:>12}    {:>12}".format("Index", "Reference", "Computed", "Diff.",  "Rel. diff."))
            print("-"*63)
            for idx in ref[pol][angle]:
                r_val = ref[pol][angle][idx]
                c_val = comp[pol][angle].get(idx, 0)
                diff = c_val - r_val
                reldiff = diff/r_val * 100 if r_val !=0 else 1
                if r_val !=0:
                    print("{:<6} {:>12.6f} {:>12.6f} {:>12.6f} {:>12.4f} %".format(idx, r_val, c_val, diff, reldiff))
                else:
                    print("{:<6} {:>12.6f} {:>12.6f} {:>12.6f}          -- ".format(idx, r_val, c_val, diff))
                
# Run display
display_results(reference_results, computed_results)
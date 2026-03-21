#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.2.0
# License: MIT
# See the documentation at gyptis.gitlab.io

"""
Thin-film lithium niobate waveguide
===================================

Periodically-poled lithium niobate ridge waveguide.

"""

from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import refidx as rd
from scipy.spatial.transform import Rotation

import gyptis as gy

##############################################################################
# Anisotropic refractive index of LN
# https://link.springer.com/content/pdf/10.1007/s00340-008-2998-2.pdf
# Temperature and wavelength dependent refractive index equations for MgO-doped congruent and stoichiometric LiNbO3
# o. gayer,u z. sacks e. galun, a. arie
# 5% MgO dope LN


def LN_e(wl, T=25):
    a = [5.756, 0.0983, 0.2020, 189.32, 12.52, 1.32e-2]
    b = [2.86e-6, 4.7e-8, 6.113e-8, 1.516e-4]
    f = (T - 24.5) * (T + 570.82)

    n = np.sqrt(
        a[0]
        + b[0] * f
        + (a[1] + b[1] * f) / (wl**2 - (a[2] + b[2] * f) ** 2)
        + (a[3] + b[3] * f) / (wl**2 - a[4] ** 2)
        - a[5] * wl**2
    )
    return n


def LN_o(wl, T=25):
    a = [5.653, 0.1185, 0.2091, 89.61, 10.85, 1.97e-2]
    b = [7.94e-7, 3.134e-8, -4.641e-9, -2.188e-6]
    f = (T - 24.5) * (T + 570.82)

    n = np.sqrt(
        a[0]
        + b[0] * f
        + (a[1] + b[1] * f) / (wl**2 - (a[2] + b[2] * f) ** 2)
        + (a[3] + b[3] * f) / (wl**2 - a[4] ** 2)
        - a[5] * wl**2
    )
    return n


#################################################################
# Silicon dioxide refractive index

db = rd.DataBase()
sio2 = db.materials["main"]["SiO2"]["Lemarchand"]

#################################################################
# Parameters

pi = np.pi

ncore = 2.31**0.5
nclad = 1
nsub = nclad = sio2.get_index(1).real

pmesh = 5
wavelength = 1.7

sidewall_angle = 12

wtop = 1.2
wg_thickness = 0.3
wbot = wtop + 2 * np.tan(sidewall_angle * pi / 180) * wg_thickness
box_width = 1 * wbot + 2 * wavelength
hsub = 1 * wavelength
hsup = 1 * wavelength + wg_thickness
hlayer = 0.5 - wg_thickness
lmin = wavelength / pmesh
pml_width = wavelength, wavelength

n_eig = 8
Nwl = 30
wls = np.linspace(0.6, 1.7, Nwl)


#################################################################
# Geometry

thicknesses = OrderedDict(substrate=hsub, layer=hlayer, superstrate=hsup)


geom = gy.geometry.LayeredBoxPML2D(
    box_width, thicknesses=thicknesses, pml_width=pml_width
)

sup = geom.layers["superstrate"]
sub = geom.layers["substrate"]
layer = geom.layers["layer"]

y0 = geom.y_position["superstrate"]
core = geom.add_polygon(
    [
        [-wbot / 2, y0, 0],
        [-wtop / 2, y0 + wg_thickness, 0],
        [wtop / 2, y0 + wg_thickness, 0],
        [wbot / 2, y0, 0],
    ]
)

out = geom.fragment(core, [sup, layer])
core = out[0]
sup, layer = out[1:]
geom.add_physical(core, "core")
geom.add_physical(layer, "layer")
geom.add_physical(sup, "superstrate")
[geom.set_size(pml, lmin * 1) for pml in geom.pmls]
geom.set_size("superstrate", lmin / nclad)
geom.set_size("substrate", lmin / nsub)
geom.set_size("layer", lmin / ncore)
geom.set_size("core", lmin / ncore * 0.5)
geom.build()


def plot_geom(color="w"):
    geom.plot_subdomains(c=color, lw=1)


geom.plot_mesh()
plot_geom(color="r")


########################################
# Materials


def build_epsilon(wl):
    eps_core_aniso = np.diag([LN_e(wl) ** 2, LN_o(wl) ** 2, LN_o(wl) ** 2])
    nsub = nclad = sio2.get_index(wl)
    epsilon = dict(
        superstrate=nclad**2,
        core=eps_core_aniso,
        layer=eps_core_aniso,
        substrate=nsub**2,
    )
    return epsilon


plt.figure()
plt.plot(wls * 1000, LN_o(wls), "-", c="#be4848", label="$n_o$")
plt.plot(wls * 1000, LN_e(wls), "-", c="#489bbe", label="$n_e$")
plt.plot(wls * 1000, sio2.get_index(wls), "-", c="#3a8b45", label="$n_{SiO2}$")
plt.xlabel(r"Wavelength $\lambda$ (nm)")
plt.ylabel(r"LN index")
# plt.xlim(0, 15)
# plt.ylim(2.05, 2.31)
plt.legend()
plt.tight_layout()


########################################
# Eigensolver


def run(wls):
    simus = []
    effective_indices = np.zeros((Nwl, n_eig), dtype=complex)
    for i, wl in enumerate(wls):

        epsilon = build_epsilon(wl)
        wavenumber = 2 * np.pi / wl
        k_target = wavenumber * 2.2 * 1.02
        simu = gy.Waveguide(
            geom,
            epsilon=epsilon,
            wavenumber=wavenumber,
            degree=(1, 1),
        )
        simu.eigensolve(
            n_eig=n_eig,
            target=k_target,
            tol=1e-6,
            maximum_iterations=15,
        )
        evs = simu.solution["eigenvalues"]
        modes = simu.solution["eigenvectors"]
        neff = evs / wavenumber
        effective_indices[i, : len(neff)] = neff
        effective_indices[i, len(neff) :] = np.nan + 1j * np.nan
        simus.append(simu)
    return simus, effective_indices


simus_wls, effective_indices_wls = run(wls)
effective_indices_wls[effective_indices_wls.imag > 1e-6] = np.nan + 1j * np.nan


##############################################################################
# Recover results given in :cite:p:`mckenna2022` (Fig. 1c).


data_fig = np.loadtxt(f"data_LN.csv", delimiter=",", skiprows=1, usecols=[0, 1]).T

plt.figure()
plt.plot(data_fig[0], data_fig[1], ".k", ms=1, label="reference")
plt.plot(wls * 1000, effective_indices_wls, "-", c="#be4848", label="gyptis")

handles, labels = plt.gca().get_legend_handles_labels()
unique = dict(zip(labels, handles))
plt.legend(unique.values(), unique.keys())
plt.xlabel(r"Wavelength $\lambda$ (nm)")
plt.ylabel(r"Effective index $n_{\rm eff}$")
plt.tight_layout()


########################################
# Plot fields


for wl in [1.025, 2.050]:

    simus, effective_indices = run([wl])
    neff = effective_indices[0]
    simu = simus[0]
    modes = simu.solution["eigenvectors"]

    modes_plot = [0]

    for iplot in modes_plot:

        htot = geom.total_thickness
        title = [r"$|E_x|$", r"$|E_y|$", r"$|E_z|$"]
        fig, ax = plt.subplots(1, 3, figsize=(14, 4))
        E = modes[iplot]
        for j in range(3):
            plt.sca(ax[j])
            mappa = gy.dolfin.plot(E[j].module, cmap="inferno")
            plot_geom()
            plt.xlim(-box_width / 2, box_width / 2)
            plt.ylim(-htot / 2, htot / 2)
            plt.title(title[j])
            plt.colorbar(mappa)
            plt.axis("off")
        plt.suptitle(rf"$\lambda=${wl*1000:.0f}nm, $n_{{eff}}=${neff[iplot]:.3f}")
        plt.tight_layout()

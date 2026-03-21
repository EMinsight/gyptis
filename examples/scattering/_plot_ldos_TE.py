#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.4
# License: MIT
# See the documentation at gyptis.gitlab.io

"""
Local density of states
=======================

Calculation of the Green's function and LDOS in 2D finite photonic crystals.
"""

# sphinx_gallery_thumbnail_number = 2

import matplotlib.pyplot as plt
import numpy as np

import gyptis as gy
from gyptis import Dipole, LineSource, dolfin

# gy.dolfin.parameters["form_compiler"]["quadrature_degree"] = 8

##############################################################################
# Reference results are taken from :cite:p:`Asatryan2001`.


##############################################################################
# Build and mesh the geometry:

L = 8
Lmax = 0.9 * L


def create_geometry(
    rod_positions, radius, wavelength, pml_width, group=False, n_cyl=1, n_bg=1
):
    lmin = wavelength / pmesh

    geom = gy.BoxPML(
        dim=2,
        box_size=(2 * L, 2 * L),
        pml_width=(pml_width, pml_width),
    )
    box = geom.box
    cylinders = []
    for pos in rod_positions:
        cyl = geom.add_circle(*pos, 0, radius)
        cylinders.append(cyl)
    *cylinders, box = geom.fragment(cylinders, box)
    geom.add_physical(box, "box")
    [geom.set_size(pml, lmin * 1) for pml in geom.pmls]
    geom.set_size("box", lmin / n_bg)
    if group:
        geom.add_physical(cylinders, "cylinders")
        geom.set_size("cylinders", lmin / n_cyl)
    else:
        # we could define physical domains for each rod but that is slower
        # when assembling and solving the sctattering problem
        for i, cyl in enumerate(cylinders):
            geom.add_physical(cyl, f"cylinder_{i}")
            geom.set_size(f"cylinder_{i}", lmin / n_cyl)
    geom.set_size("box", lmin / n_bg)
    geom.build()
    return geom


def plot_rods(ax, rod_positions, radius):
    for pos in rod_positions:
        circle = plt.Circle(pos, radius, fill=False)
        ax.add_patch(circle)


##############################################################################
# For TE polarization, it is possible to form a band gap with air cylinders
# in a dense, homogeneous matrix and to generate a full band gap with
# a hexagonal array.


plt.close("all")
plt.ion()
n_bg = 1**0.5
n_cyl = n_bg  # index of the rods

pmesh = 10
d = 1

wavelength = 3 * d
pulsation = 2 * np.pi * gy.c / wavelength
# radius = 0.48 * d
radius = (0.48 / np.pi) ** 0.5 * d**2


rod_positions = []
for i in range(-4, 5):
    I = 9 - abs(i)
    for j in range(0, I):
        posx = i * 3**0.5 / 2
        posy = j - I / 2 + 0.5
        pos = posx, posy
        rod_positions.append(pos)

rod_positions = np.array(rod_positions) * d

geom = create_geometry(
    rod_positions,
    radius,
    wavelength,
    pml_width=wavelength,
    group=True,
    n_cyl=n_cyl,
    n_bg=n_bg,
)


source_pos = 0, 0

epsilon = {d: n_cyl**2 for d in geom.domains}
epsilon["box"] = n_bg**2

ldos = 0
for comp in range(2):

    # comp = 1
    angle = comp * np.pi / 2

    dipole = gy.Dipole(
        wavelength=wavelength,
        # phase=np.pi/2,
        amplitude=1,
        position=source_pos,
        domain=geom.mesh,
        angle=angle,
        degree=2,
    )

    s = gy.Scattering(geom, epsilon, source=dipole, degree=2, polarization="TE")

    s.solve()

    u = s.solution["total"]
    dual = s.formulation.get_dual(u)

    V = dolfin.FunctionSpace(s.mesh, "CG", s.formulation.degree)
    G = gy.project(dual[comp].imag, V)

    v = gy.dolfin.ln(abs(G)) / gy.dolfin.ln(10)
    vplot = gy.project_iterative(
        v,
        s.formulation.real_function_space,
    )
    vplot = G
    fig, ax = plt.subplots()
    cs = gy.dolfin.plot(vplot, mode="contourf", cmap="Spectral_r", levels=31)
    plot_rods(ax, rod_positions, radius)
    plt.axis("square")
    plt.xlabel(r"$x/d$")
    plt.ylabel(r"$y/d$")
    # plt.xlim(-Lmax, Lmax)
    # plt.ylim(-Lmax, Lmax)
    plt.colorbar(cs, fraction=0.04, pad=0.08)
    plt.title(r"$\log_{10}|G\,|$")
    plt.plot(*dipole.position, "xk")
    plt.tight_layout()
    plt.show()
    val = G(source_pos)

    print(val)

    ldos += -2 * pulsation / (np.pi * gy.c**2) * val

ldos_norm = (ldos) * gy.pi * gy.c**2 / (2 * pulsation * n_bg**2)

print(ldos_norm)


##############################################################################
# Due to symmetry we will only compute the LDOS for 1/8th of the domain.

nx, ny = 10, 10

X = np.linspace(0, 7, nx)
Y = np.linspace(0, 7, ny)
ldos = np.zeros((nx, ny))


# if True:
def _local_density_of_states_TE(self, x, y):
    print("=======================")
    print(f"Coordinate ({x}, {y})")
    # greens_tensor = np.zeros((2,2), dtype=complex)

    trace_greens_tensor = 0
    for comp in [0, 1]:
        angle = comp * np.pi / 2
        dipole = Dipole(
            wavelength=wavelength,
            position=(x, y),
            domain=geom.mesh,
            # phase=0,
            degree=2,
            angle=angle,
        )

        self = gy.Scattering(geom, epsilon, source=dipole, degree=2, polarization="TE")
        # self.source = dipole

        # self = gy.Scattering(geom, epsilon, source=dipole, degree=2, polarization="TE")

        # if False:#hasattr(self, "solution"):
        #     self.assemble_rhs()
        #     self.solve_system(again=True)
        # else:
        #     self.solve()
        self.solve()
        u = self.solution["total"]
        eps = dolfin.DOLFIN_EPS_LARGE
        delta = 1  # + eps
        evalpoint = x * delta, y * delta
        # if evalpoint[0] == 0:
        #     evalpoint = eps, evalpoint[1]
        # if evalpoint[1] == 0:
        #     evalpoint = evalpoint[0], eps
        # print("solved")
        dual = self.formulation.get_dual(u)
        V = dolfin.FunctionSpace(self.mesh, "CG", self.formulation.degree)
        # V = dolfin.FunctionSpace(self.mesh, "DG", 0)
        # V = self.formulation.real_function_space
        G = gy.project(dual[comp].imag, V)
        val = G(evalpoint)
        print(f"> comp {comp}= {val}")
        trace_greens_tensor -= val
    # print(v(evalpoint))
    ldos = -2 * pulsation / (np.pi * gy.c**2) * trace_greens_tensor
    print("normalized LDOS:", ldos / gy.pi * gy.c**2 / (2 * pulsation * n_bg**2))
    return ldos


for j, y in enumerate(Y):
    for i, x in enumerate(X):
        ldos[i, j] = _local_density_of_states_TE(s, x, y) if j <= i else ldos[j, i]
        xs


##############################################################################
# Rearrange the map and visualize it.

X = np.linspace(-Lmax, Lmax, 2 * nx - 1)
Y = np.linspace(-Lmax, Lmax, 2 * ny - 1)
LX = np.vstack([np.flipud(ldos[1:, :]), ldos])
LDOS = np.hstack([np.fliplr(LX[:, 1:]), LX])

v = np.log10(abs(LDOS) * gy.pi * gy.c**2 / (2 * pulsation * n_bg**2))

# fig, ax = plt.subplots(figsize=(2.6, 2.2))
fig, ax = plt.subplots()
cs = plt.contourf(X, Y, v, cmap="Spectral_r", levels=31)
plot_rods(ax, rod_positions, radius)
plt.xlim(-Lmax, Lmax)
plt.ylim(-Lmax, Lmax)
plt.axis("square")
plt.xlabel(r"$x/d$")
plt.ylabel(r"$y/d$")
plt.colorbar(cs, fraction=0.04, pad=0.08)
plt.title(r"$\log_{10}(\rho \pi c^2/2\omega)$")
plt.tight_layout()

# -*- coding: utf-8 -*-
"""
Core shell nanorod
==================

Scattering by a dielectric cylinder coated with silver.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import c

from gyptis import BoxPML, Scattering
from gyptis.source import PlaneWave

plt.ion()


##############################################################################
# Reference results are taken from [Jandieri2015]_.
# We first define a function for the Drude Lorentz model of silver permittivity.


def epsilon_silver(omega):
    eps_inf = 3.91
    omega_D = 13420e12
    gamma_D = 84e12
    Omega_L = 6870e12
    Gamma_L = 12340e12
    delta_eps = 0.76
    epsilon = (
        eps_inf
        - omega_D ** 2 / (omega * (omega + 1j * gamma_D))
        - delta_eps
        * Omega_L ** 2
        / ((omega ** 2 - Omega_L ** 2) + 1j * Gamma_L * omega)
    )
    return np.conj(epsilon)


wavelength_min = 250
wavelength_max = 1000
wl = np.linspace(wavelength_min, wavelength_max, 100)
omega = 2 * np.pi * c / (wl * 1e-9)
epsAg = epsilon_silver(omega)
plt.plot(wl, epsAg.real, label="Re", c="#7b6eaf")
plt.plot(wl, epsAg.imag, label="Im", c="#c63c71")
plt.xlabel("wavelength (nm)")
plt.ylabel("silver permittivity")
plt.legend()
plt.tight_layout()

##############################################################################
# Now we create the geometry and mesh

pmesh = 15
wavelength = 452
eps_core = 2


def create_geometry(wavelength, pml_width):
    R1 = 60
    R2 = 30
    Rcalc = 2 * R1
    lmin = wavelength / pmesh
    omega = 2 * np.pi * c / (wavelength * 1e-9)
    epsAg = epsilon_silver(omega)

    nAg = abs(epsAg.real) ** 0.5
    ncore = abs(eps_core.real) ** 0.5

    lbox = Rcalc * 2 * 1.1
    geom = BoxPML(
        dim=2,
        box_size=(lbox, lbox),
        pml_width=(pml_width, pml_width),
        Rcalc=Rcalc,
    )
    box = geom.box
    shell = geom.add_circle(0, 0, 0, R1)
    out = geom.fragment(shell, box)
    box = out[1:3]
    shell = out[0]
    core = geom.add_circle(0, 0, 0, R2)
    core, shell = geom.fragment(core, shell)
    geom.add_physical(box, "box")
    geom.add_physical(core, "core")
    geom.add_physical(shell, "shell")
    [geom.set_size(pml, lmin * 0.7) for pml in geom.pmls]
    geom.set_size("box", lmin)
    geom.set_size("core", lmin / ncore)
    geom.set_size("shell", lmin / nAg)
    geom.build()
    return geom


geom = create_geometry(wavelength, pml_width=wavelength)


##############################################################################
# Define the incident plane wave and materials

pw = PlaneWave(wavelength=wavelength, angle=0, dim=2, domain=geom.mesh, degree=2)
omega = 2 * np.pi * c / (wavelength * 1e-9)
epsilon = dict(box=1, core=eps_core, shell=epsilon_silver(omega))
mu = dict(box=1, core=1, shell=1)


##############################################################################
# Scattering problem

s = Scattering(
    geom,
    epsilon,
    mu,
    pw,
    degree=2,
    polarization="TM",
)
s.solve()
s.plot_field()
geom.plot_subdomains()


##############################################################################
# Compute cros sections and check energy conservation (optical theorem)

cs = s.get_cross_sections()
assert np.allclose(cs["extinction"], cs["scattering"] + cs["absorption"], rtol=1e-2)
print(cs["extinction"])
print(cs["scattering"] + cs["absorption"])


geom = create_geometry(wavelength_min, pml_width=wavelength_max)


def cs_vs_wl(wavelength):
    pw = PlaneWave(wavelength=wavelength, angle=0, dim=2, domain=geom.mesh, degree=2)
    omega = 2 * np.pi * c / (wavelength * 1e-9)
    epsilon = dict(box=1, core=2, shell=epsilon_silver(omega))
    s = Scattering(
        geom,
        epsilon,
        mu,
        pw,
        degree=2,
        polarization="TM",
    )
    s.solve()
    cs = s.get_cross_sections()
    print(cs)
    return cs["scattering"], cs


from gyptis.sample import adaptive_sampler

wl = np.linspace(wavelength_min, wavelength_max, 20)
wla, out = adaptive_sampler(cs_vs_wl, wl)
cs = [_[1] for _ in out]
scs = np.array([d["scattering"] for d in cs])
acs = np.array([d["absorption"] for d in cs])
ecs = np.array([d["extinction"] for d in cs])

benchmark_scs = np.loadtxt("scs_r2_30nm.csv", delimiter=",")
benchmark_acs = np.loadtxt("acs_r2_30nm.csv", delimiter=",")
plt.figure()
plt.plot(
    benchmark_scs[:, 0],
    benchmark_scs[:, 1],
    "-",
    alpha=0.5,
    lw=6,
    c="#df6482",
    label="scatt. ref.",
)
plt.plot(wla, scs, c="#df6482", label="scatt. gyptis")
plt.plot(
    benchmark_acs[:, 0],
    benchmark_acs[:, 1],
    "-",
    alpha=0.5,
    lw=6,
    c="#6e8cd0",
    label="abs. ref.",
)
plt.plot(wla, acs, c="#6e8cd0", label="abs. gyptis")
plt.xlabel("wavelength (nm)")
plt.ylabel("cross sections (nm)")
plt.legend()
plt.tight_layout()

# plt.figure()
# B = (scs + acs) / ecs
# plt.plot(wla, B)


######################################################################
#
# .. [Jandieri2015] V. Jandieri, P. Meng, K. Yasumoto, and Y. Liu,
#   Scattering of light by gratings of metal-coated nanocylinders on dielectric substrate.
#   Journal of the Optical Society of America A, vol. 32, p. 1384, (2015).
#   `<https://www.doi.org/10.1364/JOSAA.32.001384>`_

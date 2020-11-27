#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# License: MIT

from collections import OrderedDict

import numpy as np
from numpy.linalg import inv
from scipy.constants import c, epsilon_0, mu_0

pi = np.pi


def get_coeffs_stack(config, lambda0, theta0, phi0, psi0):

    k0 = 2 * pi / lambda0
    omega = k0 * c

    eps = [d["epsilon"] for d in config.values()]
    mu = [d["mu"] for d in config.values()]
    thicknesses = [d["thickness"] for d in config.values() if "thickness" in d.keys()]

    #
    alpha0 = k0 * np.sin(theta0) * np.cos(phi0)
    beta0 = k0 * np.sin(theta0) * np.sin(phi0)
    gamma0 = k0 * np.cos(theta0)
    Ex0 = np.cos(psi0) * np.cos(theta0) * np.cos(phi0) - np.sin(psi0) * np.sin(phi0)
    Ey0 = np.cos(psi0) * np.cos(theta0) * np.sin(phi0) + np.sin(psi0) * np.cos(phi0)
    Ez0 = -np.cos(psi0) * np.sin(theta0)

    def _matrix_pi(M, gamma):
        q = gamma * M
        return np.array(
            [
                [1, 1, 0, 0],
                [0, 0, 1, 1],
                [q[0, 1], -q[0, 1], -q[0, 0], q[0, 0]],
                [q[1, 1], -q[1, 1], -q[1, 0], q[1, 0]],
            ],
            dtype=complex,
        )

    def _matrix_t(gamma, e):
        t = np.zeros((4, 4), dtype=complex)
        t[0, 0] = t[2, 2] = np.exp(1j * gamma * e)
        t[1, 1] = t[3, 3] = np.exp(-1j * gamma * e)
        return t

    def _matrix_B(eps, mu):
        eps *= epsilon_0
        mu *= mu_0
        return np.array(
            [
                [omega * mu, 0, beta0],
                [0, omega * mu, -alpha0],
                [-beta0, alpha0, -omega * eps],
            ]
        )

    gamma = [
        np.sqrt(k0 ** 2 * e * m - alpha0 ** 2 - beta0 ** 2) for e, m in zip(eps, mu)
    ]
    B = [_matrix_B(e, m) for e, m in zip(eps, mu)]
    M = [inv(b) for b in B]
    Pi = [_matrix_pi(m, g) for m, g in zip(M, gamma)]
    T_ = [_matrix_t(g, e) for g, e in zip(gamma[1:-1], thicknesses)]
    # T.append(np.eye(4))
    Tr = T_ + [np.eye(4)]
    # T = [np.eye(4)] + T_

    M1 = np.eye(4)
    p_prev = Pi[0]
    for p, t in zip(Pi[1:], Tr):
        M1 = inv(t) @ inv(p) @ p_prev @ M1
        p_prev = p

    K = inv(M1)
    Q = np.array(
        [
            [K[0, 0], 0, K[0, 2], 0],
            [K[1, 0], -1, K[1, 2], 0],
            [K[2, 0], 0, K[2, 2], 0],
            [K[3, 0], 0, K[3, 2], -1],
        ],
        dtype=complex,
    )

    ## solve
    U0 = np.array([Ex0, 0, Ey0, 0], dtype=complex)
    sol = inv(Q) @ U0

    # get coefficients by recurrence
    phi_0 = np.array([Ex0, sol[1], Ey0, sol[3]])
    phi_end = np.array([sol[0], 0, sol[2], 0])
    p_prev = Pi[0]
    phi_prev = phi_0
    phi = [phi_0]

    for p, t in zip(Pi[1:], Tr):
        phi_j = inv(t) @ inv(p) @ p_prev @ phi_prev
        phi.append(phi_j)
        p_prev = p
        phi_prev = phi_j

    # assert np.all(np.abs(phi_j - phi_end)<1e-14)

    ## Ez
    for i, (p, g, m) in enumerate(zip(phi.copy(), gamma, M)):
        phiz_plus = (m[2, 0] * p[2] - m[2, 1] * p[0]) * g
        phiz_minus = (m[2, 1] * p[1] - m[2, 0] * p[3]) * g
        phixh_plus = (m[0, 0] * p[2] - m[0, 1] * p[0]) * g
        phixh_minus = (m[0, 1] * p[1] - m[0, 0] * p[3]) * g
        phiyh_plus = (m[1, 0] * p[2] - m[1, 1] * p[0]) * g
        phiyh_minus = (m[1, 1] * p[1] - m[1, 0] * p[3]) * g
        phizh_plus = (m[2, 1] * phixh_plus - m[2, 0] * phiyh_plus) * g
        phizh_minus = (m[2, 0] * phiyh_minus - m[2, 1] * phixh_minus) * g
        phi[i] = np.append(
            phi[i],
            [
                phiz_plus,
                phiz_minus,
                phixh_plus,
                phixh_minus,
                phiyh_plus,
                phiyh_minus,
                phizh_plus,
                phizh_minus,
            ],
        )

    R = (
        1.0
        / gamma[0] ** 2
        * (
            (gamma[0] ** 2 + alpha0 ** 2) * abs(phi[0][1]) ** 2
            + (gamma[0] ** 2 + beta0 ** 2) * abs(phi[0][3]) ** 2
            + 2 * alpha0 * beta0 * np.real(phi[0][1] * phi[0][3].conjugate())
        )
    )
    T = (
        1.0
        / (gamma[0] * gamma[-1] * mu[-1])
        * (
            (gamma[-1] ** 2 + alpha0 ** 2) * abs(phi[-1][0]) ** 2
            + (gamma[-1] ** 2 + beta0 ** 2) * abs(phi[-1][2]) ** 2
            + 2 * alpha0 * beta0 * np.real(phi[-1][0] * phi[-1][2].conjugate())
        )
    )

    losses = np.array(eps).imag

    P0 = 0.5 * np.sqrt(epsilon_0 / mu_0) * np.cos(theta0)

    # q = [l * (sum(abs(p) ** 2)) for l, p in zip(losses, phi)]

    th = [0] + thicknesses + [0]
    tcum = np.cumsum([0] + thicknesses).tolist()
    tcum += [tcum[-1]]

    q = [
        l * e * sum(abs(p) ** 2)
        + 2
        * l
        * np.real(
            p[0]
            * p[1].conj()
            # * np.exp(-2j * g * zi)
            * (np.exp(-2j * g * zi) - 1)
            / (2j * g)
        )
        for l, p, e, zi, g in zip(losses, phi, th, tcum, gamma)
    ]

    Q_ = [-0.5 * epsilon_0 * omega / P0 * q_ for q_ in q]

    Q = sum(Q_)
    # print(Q_)
    # print(R, T, Q, R + T + Q)

    return phi, alpha0, beta0, gamma, R, T


import dolfin as df

from gyptis.sources import *


def field_stack_3D(phi, alpha0, beta0, gamma, zshift=0, degree=1, domain=None):

    Kplus = vector(sp.symbols("alpha0, beta0, -gamma", real=True))
    Kminus = vector(sp.symbols("alpha0, beta0, gamma", real=True))
    deltaZ = vector((0, 0, sp.symbols("z0", real=True)))

    Prop_plus = sp.exp(1j * Kplus.dot(X - deltaZ))
    Prop_minus = sp.exp(1j * Kminus.dot(X - deltaZ))

    def build(P):
        re, im = P.as_real_imag()
        code = [sp.printing.ccode(p) for p in (re, im)]
        e = df.Expression(
            code,
            alpha0=alpha0,
            beta0=beta0,
            gamma=gamma,
            z0=zshift,
            degree=degree,
            domain=domain,
        )
        return Complex(e[0], e[1])

    prop_plus = build(Prop_plus)
    prop_minus = build(Prop_minus)

    Phi_plus = Complex(df.as_tensor([*phi[0::2].real]), df.as_tensor([*phi[0::2].imag]))
    Phi_minus = Complex(
        df.as_tensor([*phi[1::2].real]), df.as_tensor([*phi[1::2].imag])
    )
    E_plus = Phi_plus * prop_plus
    E_minus = Phi_minus * prop_minus
    return E_plus + E_minus


def field_stack_2D(phi, alpha0, beta, yshift=0, degree=1, domain=None):

    Kplus = vector(sp.symbols("alpha0, beta, 0", real=True))
    Kminus = vector(sp.symbols("alpha0, -beta, 0", real=True))
    deltaY = vector((0, sp.symbols("y0", real=True), 0))

    Prop_plus = sp.exp(1j * Kplus.dot(X - deltaY))
    Prop_minus = sp.exp(1j * Kminus.dot(X - deltaY))

    def build(P):
        re, im = P.as_real_imag()
        re, im = (p.subs(x[2], 0) for p in (re, im))
        code = [sp.printing.ccode(p) for p in (re, im)]
        e = df.Expression(
            code,
            alpha0=alpha0,
            beta=beta,
            y0=yshift,
            degree=degree,
            domain=domain,
        )
        return Complex(e[0], e[1])

    prop_plus = build(Prop_plus)
    prop_minus = build(Prop_minus)

    Phi_plus = Complex(phi[0].real, phi[0].imag)
    Phi_minus = Complex(phi[1].real, phi[1].imag)
    E_plus = Phi_plus * prop_plus
    E_minus = Phi_minus * prop_minus
    return E_plus + E_minus


if __name__ == "__main__":

    import matplotlib.pyplot as plt

    lambda0 = 1.1
    theta0 = -0.0 * pi
    phi0 = 0 * pi / 3
    psi0 = 0 * pi

    config = OrderedDict(
        {
            "superstrate": {"epsilon": 1, "mu": 1},
            "layer 1": {"epsilon": 2.3 - 0.2j, "mu": 2, "thickness": 1.7},
            "layer 2": {"epsilon": 3.5, "mu": 1, "thickness": 0.5},
            "layer 3": {"epsilon": 8.6 - 0.3j, "mu": 1, "thickness": 0.1},
            "substrate": {"epsilon": 3, "mu": 1.0},
        }
    )

    phi, alpha0, beta0, gamma, R, T = get_coeffs_stack(
        config, lambda0, theta0, phi0, psi0
    )
    thicknesses = [d["thickness"] for d in config.values() if "thickness" in d.keys()]

    tcum = np.cumsum([0] + thicknesses).tolist()
    tcum += [tcum[-1]]

    # tcum = np.cumsum( thicknesses + [0]).tolist()
    # tcum = [tcum[0]] + tcum

    #
    #
    # Estack = [
    #     field_stack_2D(p, alpha0, g, yshift=e) for p, g, e in zip(phi, gamma, tcum)
    # ]

    z = np.linspace(-3, 1, 100000)
    zshift = 0  # -sum(thicknesses)
    z1 = -z
    prop_plus = [np.exp(-1j * g * z1) for g in gamma]
    prop_minus = [np.exp(1j * g * z1) for g in gamma]

    plt.ion()
    plt.clf()
    msk = np.zeros_like(z)
    zi = 0
    msk[z1 <= zi] = 1
    mask = [msk]
    for t in thicknesses:
        msk = np.zeros_like(z)
        msk[(z1 > zi) & (z1 <= zi + t)] = 1
        mask.append(msk)
        zi += t
    msk = np.zeros_like(z)
    msk[(z1 > zi)] = 1
    mask.append(msk)

    # mask=np.flipud(mask)

    [plt.plot(z, m + 1, c="#d7d7d7") for m in mask]
    E = []

    for pp, pm, p, m, e, g in zip(prop_plus, prop_minus, phi, mask, tcum, gamma):

        dp, dm = np.exp(1j * g * e), np.exp(-1j * g * e)
        pp_ = pp * p[0] * dp + pm * p[1] * dm
        E.append(pp_ * m)

    # E = np.fliplr(E)
    # [plt.plot(z1, e) for e in Elay]
    # plt.plot(z, np.real(sum(E)),"-")
    # plt.plot(z, np.imag(sum(E)),"--")

    Einc = mask[0] * phi[0][0] * prop_plus[0]
    Etot = sum(E)
    Ediff = Etot - Einc
    plt.plot(z, np.abs(Etot) ** 2, "k")
    plt.plot(z, np.abs(Ediff) ** 2, "r")

    plt.plot(z, np.real(Ediff), "g-")
    plt.plot(z, np.imag(Ediff), "g--")

    losses = [d["epsilon"].imag for d in config.values() if "epsilon" in d.keys()]

    epsilon_0
    k0 = 2 * pi / lambda0
    omega = k0 * c

    P0 = 0.5 * np.sqrt(epsilon_0 / mu_0) * np.cos(theta0)

    q = [
        -0.5 * epsilon_0 * omega / P0 * np.trapz(l * abs(e) ** 2, z)
        for l, e in zip(losses, E)
    ]

    Q = np.sum(q)
    print(q)
    print(Q)

    print(R + T + Q)

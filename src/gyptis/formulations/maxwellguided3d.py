#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.3
# License: MIT
# See the documentation at gyptis.gitlab.io


from .maxwell3d import *

zvec = Constant((0, 0, 1))


class MaxwellGuided3D(Maxwell3D):
    def __init__(self, *args, wavenumber=0, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.modal:
            raise NotImplementedError("Only modal analysis is implemented")
        self.wavenumber = wavenumber

        self._mu_inv = self.mu.invert().as_property(dim=3)
        self._epsilon = self.epsilon.as_property(dim=3)
        self._epsilon_dom = self.epsilon.as_subdomain()
        self._mu_inv_dom = self.mu.invert().as_subdomain()
        self.phasor = phasor(
            self.wavenumber,
            direction=2,
            degree=self.degree,
            domain=self.geometry.mesh,
        )

    def maxwell(self, u, v, epsilon, inv_mu, domain="everywhere"):
        epsilon = self._epsilon[domain]
        inv_mu = self._mu_inv[domain]
        k0 = Constant(self.wavenumber)
        if domain == []:
            return None
        # a₀(u,v) = ∫_Ω (∇ × v)·[μ̿⁻¹ (∇ × u)] dV
        form = [inner(inv_mu * curl(u), curl(v))]
        # a₁(u,v) = ∫_Ω {(∇ × v)·[μ̿⁻¹ (ẑ × u)] - (ẑ × v)·[μ̿⁻¹ (∇ × u)]} dV
        form.append(
            inner(inv_mu * cross(zvec, u), curl(v))
            - inner(cross(zvec, v), inv_mu * curl(u))
        )
        # a₂(u,v) = ∫_Ω (ẑ × v)·[μ̿⁻¹ (ẑ × u)] dV
        form.append(inner(inv_mu * cross(zvec, u), cross(zvec, v)))
        # m(e,v) = ∫_Ω v·[ε̿(r)u] dV
        form.append(-(k0**2) * inner(epsilon * u, v))
        return [f * self.dx(domain) for f in form]

    def _weak(self, u, v):
        formulation = 0
        for dom in self.geometry.domains.keys():
            form = self.maxwell(u, v, domain=dom)
            if form is None:
                continue
            else:
                formulation += form
        return [f.real + f.imag for f in formulation]

    @property
    def weak(self):
        return self._weak(self.trial, self.test)

    def build_boundary_conditions(self):
        self._boundary_conditions = self.build_pec_boundary_conditions(
            Constant((0, 0, 0))
        )
        return self._boundary_conditions

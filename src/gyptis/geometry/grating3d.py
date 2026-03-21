#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.2.0
# License: MIT
# See the documentation at gyptis.gitlab.io

from .geometry import *


class Layered3D(Geometry):
    def __init__(
        self,
        period=(1, 1),
        thicknesses=OrderedDict(),
        pml_thickness=(1, 1),
        **kwargs,
    ):
        super().__init__(
            dim=3,
            **kwargs,
        )
        if isinstance(period, (int, float)):
            period = (period, period)
        if isinstance(pml_thickness, (int, float)):
            pml_thickness = (pml_thickness, pml_thickness)
        thicknesses = thicknesses.copy()
        layer_names = list(thicknesses.keys())
        thicknesses["pml_z_" + layer_names[0]] = pml_thickness[0]
        thicknesses.move_to_end("pml_z_" + layer_names[0], last=False)

        thicknesses["pml_z_" + layer_names[-1]] = pml_thickness[1]
        self.pml_physical = ["pml_z_" + layer_names[0], "pml_z_" + layer_names[-1]]
        self.pml_thickness = pml_thickness
        self.period = period
        self.thicknesses = thicknesses

        self.periodic_tol = 1e-6

        self.translation_x = self._translation_matrix([self.period[0], 0, 0])
        self.translation_y = self._translation_matrix([0, self.period[1], 0])

        self.total_thickness = sum(self.thicknesses.values())
        dx, dy = self.period
        self.z0 = -sum(list(self.thicknesses.values())[:2])

        z0 = self.z0
        self.layers = {}
        self.z_position = {}
        for id, thickness in self.thicknesses.items():
            layer = self.make_layer(z0, thickness)
            self.layers[id] = layer
            self.z_position[id] = z0
            self.add_physical(layer, id)
            z0 += thickness

        self.remove_all_duplicates()
        self.synchronize()
        for sub, num in self.subdomains["volumes"].items():
            self.add_physical(num, sub)

    def make_layer(self, z_position, thickness):
        return self.add_box(
            -self.period[0] / 2,
            -self.period[1] / 2,
            z_position,
            self.period[0],
            self.period[1],
            thickness,
        )

    def set_periodic_mesh(self, eps=None):
        s = self.get_periodic_bnds(self.z0, self.total_thickness, eps=eps)

        periodic_id = {k: [S[-1] for S in v] for k, v in s.items()}
        gmsh.model.mesh.setPeriodic(
            2, periodic_id["+x"], periodic_id["-x"], self.translation_x
        )
        gmsh.model.mesh.setPeriodic(
            2, periodic_id["+y"], periodic_id["-y"], self.translation_y
        )
        self.periodic_bnds = periodic_id
        return periodic_id

    def build(self, set_periodic=True, **kwargs):
        if set_periodic:
            self.set_periodic_mesh()
        super().build(**kwargs)

    def get_periodic_bnds(self, z_position, thickness, eps=None):
        eps = eps or self.periodic_tol

        dx, dy = self.period

        pmin = -dx / 2 - eps, -dy / 2 - eps, z_position - eps
        pmax = -dx / 2 + eps, +dy / 2 + eps, thickness + eps
        s = {"-x": gmsh.model.getEntitiesInBoundingBox(*pmin, *pmax, 2)}
        pmin = +dx / 2 - eps, -dy / 2 - eps, z_position - eps
        pmax = +dx / 2 + eps, +dy / 2 + eps, thickness + eps
        s["+x"] = gmsh.model.getEntitiesInBoundingBox(*pmin, *pmax, 2)

        pmin = -dx / 2 - eps, -dy / 2 - eps, z_position - eps
        pmax = +dx / 2 + eps, -dy / 2 + eps, thickness + eps
        s["-y"] = gmsh.model.getEntitiesInBoundingBox(*pmin, *pmax, 2)

        pmin = -dx / 2 - eps, +dy / 2 - eps, z_position - eps
        pmax = +dx / 2 + eps, +dy / 2 + eps, thickness + eps
        s["+y"] = gmsh.model.getEntitiesInBoundingBox(*pmin, *pmax, 2)
        return s

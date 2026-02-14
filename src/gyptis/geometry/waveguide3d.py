#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.1.2
# License: MIT
# See the documentation at gyptis.gitlab.io


from gyptis.geometry import *


class LayeredBoxPML3D(Geometry):
    def __init__(
        self,
        width,
        thicknesses,
        pml_width=None,
        **kwargs,
    ):
        super().__init__(
            dim=3,
            **kwargs,
        )

        # self.cross_section = LayeredBoxPML2D(
        #     width[0], thicknesses, (pml_width[0], pml_width[1]), **kwargs
        # )

        self.build_pmls = pml_width != None
        self.build_pmls_z = pml_width[2] != None

        self.width = width
        self.thicknesses = thicknesses
        self.total_thickness = sum(self.thicknesses.values())

        self.layers = {}
        self.y_position = {}
        self.box_size = width[0], self.total_thickness, width[1]
        self.pml_width = pml_width

        y0 = -self.total_thickness / 2
        if self.build_pmls:
            tx0 = self.pml_width[0] / 2 + self.box_size[0] / 2
            if self.build_pmls_z:
                tz0 = self.pml_width[2] / 2 + self.box_size[2] / 2

        for name, thickness in self.thicknesses.items():
            layer = self.make_layer(y0, thickness)
            self.layers[name] = layer
            self.y_position[name] = y0
            self.add_physical(layer, name)
            if self.build_pmls:
                spml = (self.pml_width[0], thickness, self.width[1])
                ty = thickness / 2 + y0
                _pmls = []
                for i in [-1, 1]:
                    t = np.array([i * tx0, ty, 0])
                    _pml = self._add_box_translate(spml, t)
                    _pmls.append(_pml)
                self.add_physical(_pmls, "pml_x_" + name)
                if self.build_pmls_z:
                    spml = (self.width[0], thickness, self.pml_width[2])
                    _pmls = []
                    for i in [-1, 1]:
                        t = np.array([0, ty, i * tz0])
                        _pml = self._add_box_translate(spml, t)
                        _pmls.append(_pml)
                    self.add_physical(_pmls, "pml_z_" + name)

                    spml = (self.pml_width[0], thickness, self.pml_width[2])
                    _pmls = []
                    for i in [-1, 1]:
                        for j in [-1, 1]:
                            t = np.array([i * tx0, ty, j * tz0])
                            _pml = self._add_box_translate(spml, t)
                            _pmls.append(_pml)
                    self.add_physical(_pmls, "pml_xz_" + name)

            y0 += thickness

        if self.build_pmls:
            y0 = -self.total_thickness / 2
            names = list(self.layers.keys())

            top_bot_pos = [
                -self.pml_width[1] / 2 + y0,
                self.total_thickness + y0 + self.pml_width[1] / 2,
            ]

            for j in [0, -1]:
                tz = np.array([0, top_bot_pos[j], 0])
                spml = (self.box_size[0], self.pml_width[1], self.box_size[2])
                _pml = self._add_box_translate(spml, tz)
                self.add_physical(_pml, "pml_y_" + names[j])

                spml = (self.pml_width[0], self.pml_width[1], self.box_size[2])
                _pmls = []
                for i in [-1, 1]:
                    t = np.array([i * tx0, top_bot_pos[j], 0])
                    _pml = self._add_box_translate(spml, t)
                    _pmls.append(_pml)
                self.add_physical(_pmls, "pml_xy_" + names[j])

                if self.build_pmls_z:
                    spml = (self.box_size[0], self.pml_width[1], self.pml_width[2])
                    _pmls = []
                    for i in [-1, 1]:
                        t = np.array([0, top_bot_pos[j], i * tz0])
                        _pml = self._add_box_translate(spml, t)
                        _pmls.append(_pml)
                    self.add_physical(_pmls, "pml_yz_" + names[j])
                    
                    spml = (self.pml_width[0], self.pml_width[1], self.pml_width[2])
                    _pmls = []
                    for i in [-1, 1]:
                        for k in [-1, 1]:
                            t = np.array([i * tx0, top_bot_pos[j], k * tz0])
                            _pml = self._add_box_translate(spml, t)
                            _pmls.append(_pml)
                    self.add_physical(_pmls, "pml_xyz_" + names[j])

        self.remove_all_duplicates()

        for sub, num in self.subdomains_entities["volumes"].items():
            self.add_physical(num, sub)
        
        self._initial_setup = self._get_initial_setup()
        self._subdomains_ids = self._initial_setup[1]
    
    @property
    def subdomains_ids(self):
        return self._subdomains_ids

    @subdomains_ids.setter
    def subdomains_ids(self, subdomain_ids):
        self._restore_initial_subdomains(subdomain_ids)

    def _add_box_center(self, box_size):
        corner = -np.array(box_size) / 2
        return self.add_box(*corner, *box_size)

    def _translate(self, tag, t):
        translation = tuple(t)
        self.translate(self.dimtag(tag), *translation)

    def _add_box_translate(self, box_size, translation):
        pml = self._add_box_center(box_size)
        self._translate(pml, translation)
        return pml

    def make_layer(self, y_position, thickness):
        return self.add_box(
            -self.width[0] / 2,
            y_position,
            -self.width[1] / 2,
            self.width[0],
            thickness,
            self.width[1],
        )

    def _get_initial_setup(self):
        all_subdomains = list(self.subdomains_entities["volumes"].values())
        all_subdomains_flat = [item for sublist in all_subdomains for item in sublist]
        lengths = [len(sublist) for sublist in all_subdomains]
        all_subdomains_name = list(self.subdomains_entities["volumes"].keys())
        return all_subdomains_name, all_subdomains_flat, lengths
    

    def _restore_initial_subdomains(self, subdomain_ids):
        all_subdomains_name, _, lengths = self._initial_setup
        i = 0
        all_subdomains_restored = []
        for n in lengths:
            all_subdomains_restored.append(subdomain_ids[i : i + n])
            i += n
        for name, num in zip(all_subdomains_name, all_subdomains_restored):
            self.add_physical(num, name)


import gyptis as gy
from collections import OrderedDict
import matplotlib.pyplot as plt

plt.close("all")
plt.ion()

box_width = 8, 6
pml_width = 1, 1.2, 2
pml_width = 1, 1.2, None


wl = 1

nsub = 1.43
nsup = 1
ncore = 4
wg_width = 1
wg_thickness = 0.1
wg_depth = 2

hsup = hsub = wg_thickness * 10

pmesh = 2
lmin = wl / pmesh

thicknesses = OrderedDict(substrate=hsub, superstrate=hsup)

geom3D = LayeredBoxPML3D(box_width, thicknesses=thicknesses, pml_width=pml_width)


mid_width = wg_width * 2
mid_thickness = wg_thickness * 3
mid_depth = wg_depth / 4

ysub = geom3D.y_position["superstrate"]

design_size = 4

wg_width = 1
wg_depth1 = geom3D.box_size[2]/2 - design_size/2
wg_depth2 = geom3D.box_size[0]/2 - design_size/2

# core1 = geom3D.add_box(
#     -wg_width / 2,
#     ysub,
#     -geom3D.box_size[2]/2- geom3D.pml_width[2],
#     wg_width,
#     wg_thickness,
#     wg_depth1 + geom3D.pml_width[2],
# )

# # core2 = geom3D.add_box(
# #     design_size/2,
# #     ysub,
# #     -wg_width / 2,
# #     wg_depth2+ geom3D.pml_width[0],
# #     wg_thickness,
# #     wg_width,
# # )
# core2 = geom3D.add_box(
#     -wg_width / 2,
#     ysub,
#     design_size/2,
#     wg_width,
#     wg_thickness,
#     wg_depth1+ geom3D.pml_width[2],
# )



core1 = geom3D.add_box(
    -wg_width / 2,
    ysub,
    -geom3D.box_size[2]/2,
    wg_width,
    wg_thickness,
    wg_depth1,
)

core2 = geom3D.add_box(
    -wg_width / 2,
    ysub,
    design_size/2,
    wg_width,
    wg_thickness,
    wg_depth1,
)



design = geom3D.add_box(
    -design_size/2,
    ysub,
    -design_size/2,
    design_size,
    wg_thickness,
    design_size,
)

# fragments = geom3D.fragment([core1,design,core2], geom3D.subdomains_ids)
# core1 = fragments[1]
# design = fragments[2]
# core2 = fragments[3]
# geom3D.subdomains_ids = fragments[5:]

# geom3D.add_physical([core1,core2], "core")
# geom3D.add_physical([design], "design")
# # geom3D.add_physical([fragments[0]], "pml_z_core")
# # geom3D.add_physical([fragments[4]], "pml_x_core")
# geom3D.add_physical([fragments[0], fragments[4]], "pml_z_core")



fragments = geom3D.fragment([core1,design,core2], geom3D.subdomains_ids)
core1 = fragments[0]
design = fragments[1]
core2 = fragments[2]
geom3D.subdomains_ids = fragments[3:]

geom3D.add_physical([core1,core2], "core")
geom3D.add_physical([design], "design")

print("Building 3D mesh")
geom3D.build(1)
print("Done 3D mesh")

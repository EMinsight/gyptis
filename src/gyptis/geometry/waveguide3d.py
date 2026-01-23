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
                self.add_physical(_pmls, "pmlx_" + name)
                spml = (self.width[0], thickness, self.pml_width[2])
                _pmls = []
                for i in [-1, 1]:
                    t = np.array([0, ty, i * tz0])
                    _pml = self._add_box_translate(spml, t)
                    _pmls.append(_pml)
                self.add_physical(_pmls, "pmlz_" + name)

                spml = (self.pml_width[0], thickness, self.pml_width[2])
                _pmls = []
                for i in [-1, 1]:
                    for j in [-1, 1]:
                        t = np.array([i * tx0, ty, j * tz0])
                        _pml = self._add_box_translate(spml, t)
                        _pmls.append(_pml)
                self.add_physical(_pmls, "pmlxz_" + name)

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
                self.add_physical(_pml, "pmly_" + names[j])

                spml = (self.pml_width[0], self.pml_width[1], self.box_size[2])
                _pmls = []
                for i in [-1, 1]:
                    t = np.array([i * tx0, top_bot_pos[j], 0])
                    _pml = self._add_box_translate(spml, t)
                    _pmls.append(_pml)
                self.add_physical(_pmls, "pmlxy_" + names[j])

                spml = (self.box_size[0], self.pml_width[1], self.pml_width[2])
                _pmls = []
                for i in [-1, 1]:
                    t = np.array([0, top_bot_pos[j], i * tz0])
                    _pml = self._add_box_translate(spml, t)
                    _pmls.append(_pml)
                self.add_physical(_pmls, "pmlyz_" + names[j])

                spml = (self.pml_width[0], self.pml_width[1], self.pml_width[2])
                _pmls = []
                for i in [-1, 1]:
                    for k in [-1, 1]:
                        t = np.array([i * tx0, top_bot_pos[j], k * tz0])
                        _pml = self._add_box_translate(spml, t)
                        _pmls.append(_pml)
                self.add_physical(_pmls, "pmlxyz_" + names[j])

        self.remove_all_duplicates()

        for sub, num in self.subdomains_entities["volumes"].items():
            self.add_physical(num, sub)

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


# def build3D(geom2D, z_extrude, pmlz_thickness):
#     # geom = copy.copy(geom2D)
#     geom = geom2D.copy_instance()
#     # geom.model_name += "3D"
#     # geom.model.add(geom.model_name)
#     subdomain_ids = list(geom.subdomains_entities["surfaces"].values())
#     subdomain_names = list(geom.subdomains["surfaces"].keys())
#     to_extrude = [
#         geom.model.get_entities_for_physical_name(s)
#         for s in geom.subdomains["surfaces"]
#     ]

#     to_extrude_flat = [item for sublist in to_extrude for item in sublist]

#     geom.dim = 3
#     pmls_sub = []

#     new_sub = list(geom.new_subdomains["surfaces"].values())
#     # geom.remove(geom.dimtag(new_sub))

#     for sub, name, id in zip(to_extrude, subdomain_names, subdomain_ids):

#         # if name in geom.new_subdomains["surfaces"].keys():
#         #     print(name)
#         #     continue

#         sub1 = [d[1] for d in sub]
#         geom.add_physical(sub1, "surface_" + name, dim=2)

#         extrude_output = geom.extrude(
#             sub,
#             0,
#             0,
#             z_extrude,
#             numElements=[],
#             heights=[z_extrude],
#             recombine=False,
#             sync=False,
#         )
#         extrude_output = [dt[1] for dt in extrude_output if dt[0] == 3]

#         extrude_output_zm = geom.extrude(
#             sub,
#             0,
#             0,
#             pmlz_thickness,
#             numElements=[],
#             heights=[pmlz_thickness],
#             recombine=False,
#             sync=False,
#         )
#         extrude_output_zm = [dt[1] for dt in extrude_output_zm if dt[0] == 3]
#         extrude_output_zp = geom.extrude(
#             sub,
#             0,
#             0,
#             pmlz_thickness,
#             numElements=[],
#             heights=[pmlz_thickness],
#             recombine=False,
#             sync=False,
#         )
#         extrude_output_zp = [dt[1] for dt in extrude_output_zp if dt[0] == 3]

#         geom.translate(
#             geom.dimtag(extrude_output_zm, dim=3), 0, 0, -pmlz_thickness, sync=False
#         )

#         geom.translate(
#             geom.dimtag(extrude_output_zp, dim=3), 0, 0, z_extrude, sync=True
#         )

#         geom.add_physical(extrude_output, name, dim=3)

#         if name in geom.layers:
#             geom.layers[name] = extrude_output[0]

#         newsub = extrude_output_zp + extrude_output_zm
#         if name.startswith("pml"):
#             s = name.split("_")
#             newname = s[0] + "z_" + "_".join(s[1:])

#         else:
#             newname = "pmlz_" + name
#         pmls_sub.append(newname)
#         geom.add_physical(newsub, newname, dim=3)

#     geom.subdomains["surfaces"] = {}
#     geom.subdomains_entities["surfaces"] = {}
#     geom.pmls = pmls_sub
#     return geom


# import gyptis as gy
# from collections import OrderedDict
# import matplotlib.pyplot as plt

# plt.close("all")
# plt.ion()

# # box_width = 4, 5
# # pml_width = 1, 1.2, 2


# # self = LayeredBoxPML3D(box_width, thicknesses=thicknesses, pml_width=pml_width)

# # self.build(1)
# import gmsh


# wl = 1

# nsub = 1.43
# nsup = 1
# ncore = 4
# wg_width = 1
# wg_thickness = 0.3


# box_width = wg_width * 2
# pml_width = 2.5, 2.5

# hsup = hsub = wg_thickness * 2

# pmesh = 1
# lmin = wl / pmesh

# z_extrude = 6 * wl
# pmlz_thickness = wl

# thicknesses = OrderedDict(substrate=hsub, superstrate=hsup)
# geom = LayeredBoxPML2D(box_width, thicknesses=thicknesses, pml_width=pml_width)

# sup = geom.layers["superstrate"]
# sub = geom.layers["substrate"]
# core = geom.add_rectangle(
#     -wg_width / 2, geom.y_position["superstrate"], 0, wg_width, wg_thickness
# )
# out = geom.fragment(core, [sup, sub])

# core = out[0]
# sup, sub = out[1:]
# geom.add_physical(core, "core")
# geom.add_physical(sub, "substrate")
# geom.add_physical(sup, "superstrate")
# [geom.set_size(pml, lmin * 1) for pml in geom.pmls]
# geom.set_size("superstrate", lmin / nsup)
# geom.set_size("substrate", lmin / nsub)
# geom.set_size("core", lmin / ncore)
# geom.build()

# # geom.plot_mesh()

# epsilon = dict(superstrate=nsup**2, core=ncore**2, substrate=nsub**2)
# wavenumber = 2.2  # 2 * gy.pi / wl
# n_eig = 6
# k_target = wavenumber * ncore * 1.02

# simu = gy.Waveguide(
#     geom,
#     epsilon=epsilon,
#     wavenumber=wavenumber,
#     degree=(1, 1),
# )


# ### test extrude:

# geom2D = geom

# geom = geom2D.copy_instance()

# # geom.model_name += "3D"
# # geom.model.add(geom.model_name)
# subdomain_ids = list(geom.subdomains_entities["surfaces"].values())
# subdomain_names = list(geom.subdomains["surfaces"].keys())
# to_extrude = [
#     geom.model.get_entities_for_physical_name(s) for s in geom.subdomains["surfaces"]
# ]


# to_extrude_flat = [item for sublist in to_extrude for item in sublist]

# geom.dim = 3

# # ztot = 2 * pmlz_thickness + z_extrude

# # extrude_output = geom.extrude(
# #     to_extrude_flat,
# #     0,
# #     0,
# #     ztot,
# #     numElements=[],
# #     heights=[pmlz_thickness / ztot, z_extrude / ztot, pmlz_thickness / ztot],
# #     recombine=False,
# #     sync=True,
# # )
# # extrude_output = [dt[1] for dt in extrude_output if dt[0] == 3]
# # geom.add_physical(extrude_output, "sxsx", dim=3)


# base_surface = 1
# layers = [0.2, 0.5, 0.8, 1.5]

# out = gmsh.model.occ.extrude(
#     [(2, base_surface)],
#     0, 0, sum(layers),
#     heights=layers
# )

# gmsh.model.occ.synchronize()
# # Get only volumes (dim = 3)
# new_vols = [t for t in out if t[0] == 3]

# for i, (dim, vol) in enumerate(new_vols, start=1):
#     gmsh.model.addPhysicalGroup(3, [vol], tag=i)


# geom.build(1)

# pmls_sub = []

# new_sub = list(geom.new_subdomains["surfaces"].values())
# # geom.remove(geom.dimtag(new_sub))

# for sub, name, id in zip(to_extrude, subdomain_names, subdomain_ids):

#     # if name in geom.new_subdomains["surfaces"].keys():
#     #     print(name)
#     #     continue

#     sub1 = [d[1] for d in sub]
#     geom.add_physical(sub1, "surface_" + name, dim=2)

#     extrude_output = geom.extrude(
#         sub,
#         0,
#         0,
#         z_extrude,
#         numElements=[],
#         heights=[z_extrude],
#         recombine=False,
#         sync=False,
#     )
#     extrude_output = [dt[1] for dt in extrude_output if dt[0] == 3]

#     extrude_output_zm = geom.extrude(
#         sub,
#         0,
#         0,
#         pmlz_thickness,
#         numElements=[],
#         heights=[pmlz_thickness],
#         recombine=False,
#         sync=False,
#     )
#     extrude_output_zm = [dt[1] for dt in extrude_output_zm if dt[0] == 3]
#     extrude_output_zp = geom.extrude(
#         sub,
#         0,
#         0,
#         pmlz_thickness,
#         numElements=[],
#         heights=[pmlz_thickness],
#         recombine=False,
#         sync=False,
#     )
#     extrude_output_zp = [dt[1] for dt in extrude_output_zp if dt[0] == 3]

#     geom.translate(
#         geom.dimtag(extrude_output_zm, dim=3), 0, 0, -pmlz_thickness, sync=False
#     )

#     geom.translate(geom.dimtag(extrude_output_zp, dim=3), 0, 0, z_extrude, sync=True)

#     geom.add_physical(extrude_output, name, dim=3)

#     if name in geom.layers:
#         geom.layers[name] = extrude_output[0]

#     newsub = extrude_output_zp + extrude_output_zm
#     if name.startswith("pml"):
#         s = name.split("_")
#         newname = s[0] + "z_" + "_".join(s[1:])

#     else:
#         newname = "pmlz_" + name
#     pmls_sub.append(newname)
#     geom.add_physical(newsub, newname, dim=3)

# geom.subdomains["surfaces"] = {}
# geom.subdomains_entities["surfaces"] = {}
# geom.pmls = pmls_sub


# geom.build(1)
# xsx

# # simu.eigensolve(
# #     n_eig=n_eig,
# #     target=k_target,
# #     tol=1e-6,
# #     maximum_iterations=40,
# # )

# # ks = simu.solution["eigenvalues"]
# # neff = ks / wavenumber
# # modes = simu.solution["eigenvectors"]

# # Nmodes = len(ks)

# # print(f"Found {Nmodes} modes")
# # print(f"Effective indices {neff}")

# # comp = 0
# # comps = ["x", "y", "z"]

# # for imode in range(Nmodes):
# #     plt.figure()
# #     mapE = gy.dolfin.plot(modes[imode][comp].real, cmap="RdBu")
# #     geom.plot_subdomains(c="k", lw=1)
# #     plt.title(rf"mode {imode}: Re $E_{{{comps[comp]}}}$")
# #     plt.colorbar(mapE)
# #     plt.axis("off")
# #     plt.pause(0.01)


# # imode = 0

# #######################
# ######## 3D ########


# wg_depth = 1

# geom3D = build3D(geom, z_extrude, pmlz_thickness)
# # geom3D.remove_all_duplicates()
# geom3D.build(1)

# xsx


# sup = geom3D.layers["superstrate"]
# sub = geom3D.layers["substrate"]
# pmlz_superstrate = geom3D.subdomains["volumes"]["pmlz_superstrate"]
# pmlz_substrate = geom3D.subdomains["volumes"]["pmlz_substrate"]

# core = geom3D.add_box(
#     -wg_width / 2,
#     geom3D.y_position["superstrate"],
#     0,
#     wg_width,
#     wg_thickness,
#     wg_depth,
# )
# out = geom3D.fragment(core, [sup, sub, pmlz_superstrate, pmlz_substrate])
# # geom3D.remove_all_duplicates()

# core = out[0]
# sup, sub, pmlz_superstrate, pmlz_substrate = out[1:]
# # gmsh.model.occ.synchronize()


# geom3D.add_physical(core, "core")
# geom3D.add_physical(sub, "substrate")
# geom3D.add_physical(sup, "superstrate")
# geom3D.add_physical(pmlz_superstrate, "pmlz_superstrate")
# geom3D.add_physical(pmlz_substrate, "pmlz_substrate")


# # # [geom3D.set_size(pml, lmin * 1) for pml in geom3D.pmls]
# # geom3D.set_size("superstrate", lmin / ncore)
# # geom3D.set_size("substrate", lmin / ncore)
# # # geom3D.set_size("pmlz_core", lmin / ncore)
# # # geom3D.set_size("core", lmin / ncore)


# print("Building 3D mesh")
# geom3D.build(1)
# print("Done 3D mesh")

# V = gy.dolfin.FunctionSpace(geom.mesh, "CG", 1)


# Ez = modes[imode][comp]
# f2dre = gy.project_iterative(Ez.real, V)
# f2dre.set_allow_extrapolation(True)
# f2dim = gy.project_iterative(Ez.imag, V)
# f2dim.set_allow_extrapolation(True)

# mesh = geom3D.mesh
# V3d = gy.dolfin.FunctionSpace(mesh, "CG", 1)
# f3dre = gy.dolfin.Function(V3d)
# f3dim = gy.dolfin.Function(V3d)

# coords = V3d.tabulate_dof_coordinates().reshape((-1, 3))

# valsre = np.zeros(V3d.dim())
# valsim = np.zeros(V3d.dim())

# for i, (x, y, z) in enumerate(coords):
#     f2d = f2dre(x, y) + 1j * f2dim(x, y)
#     f2d *= np.exp(1j * wavenumber * z)
#     valsre[i] = f2d.real
#     valsim[i] = f2d.imag

# f3dre.vector().set_local(valsre)
# f3dre.vector().apply("insert")
# f3dim.vector().set_local(valsim)
# f3dim.vector().apply("insert")


# # from dolfin import *
# import numpy as np
# import vtk
# import pyvista as pv

# # --- 1. Extract mesh info ---
# points = mesh.coordinates()
# cells = mesh.cells()

# # DOLFIN legacy stores cell connectivity as an array of shape (num_cells, num_vertices_per_cell)
# # PyVista wants a flattened array with [n0, v0, v1, v2, v3, n1, v4, v5, v6, v7, ...]
# ncells = cells.shape[0]
# celltypes = np.full(ncells, pv.CellType.TETRA, dtype=np.uint8)
# connectivity = np.hstack([np.full((ncells, 1), 4, dtype=np.int64), cells]).flatten()

# # --- 2. Create PyVista grid ---
# grid = pv.UnstructuredGrid(connectivity, celltypes, points)

# # --- 3. Add scalar data from the Function ---
# vertex_values = f3dre.compute_vertex_values(mesh)
# # compute_vertex_values gives values flattened by coordinate ordering, so it matches the mesh vertices
# grid.point_data["f3dre"] = vertex_values

# # --- Define multiple z-slices ---
# z_slices = [z_extrude / 4, z_extrude / 2, 3 * z_extrude / 4]
# slices = [grid.slice(normal="z", origin=(0, 0, z)) for z in z_slices]

# slices.append(grid.slice(normal="y", origin=(0, wg_thickness / 2, 0)))
# # --- Get global scalar range (so they all use the same color scale) ---
# scalar_range = (vertex_values.min(), vertex_values.max())

# # --- Create a single plotter with shared colormap ---
# plotter = pv.Plotter()

# for sl in slices:
#     plotter.add_mesh(
#         sl,
#         scalars="f3dre",
#         cmap="RdBu",
#         clim=scalar_range,  # <== shared colormap range
#         show_scalar_bar=False,  # disable individual bars
#     )
# # --- Add one shared scalar bar ---
# plotter.add_scalar_bar(vertical=True, title=rf"mode {imode}: Re $E_{{{comps[comp]}}}$")
# plotter.add_axes()
# plotter.show_grid()
# plotter.show()


import gyptis as gy
from collections import OrderedDict
import matplotlib.pyplot as plt

plt.close("all")
plt.ion()

box_width = 4, 5
pml_width = 1, 1.2, 2


wl = 1

nsub = 1.43
nsup = 1
ncore = 4
wg_width = 1
wg_thickness = 0.1
wg_depth = 2


# box_width = wg_width * 2
# pml_width = 2.5, 2.5

hsup = hsub = wg_thickness * 10

pmesh = 2
lmin = wl / pmesh

# z_extrude = 6 * wl
# pmlz_thickness = wl

thicknesses = OrderedDict(substrate=hsub, superstrate=hsup)

# gmsh.option.setNumber("Geometry.OCCFixSmallEdges", 1)
# gmsh.option.setNumber("Geometry.OCCFixDegenerated", 1)
# gmsh.option.setNumber("Geometry.OCCSewFaces", 1)
pml_width = None
self = LayeredBoxPML3D(box_width, thicknesses=thicknesses, pml_width=pml_width)


geom3D = self
# geom3D.build(1)

# sup = geom3D.layers["superstrate"]
# sub = geom3D.layers["substrate"]
# pmlz_superstrate = geom3D.subdomains_entities["volumes"]["pmlz_superstrate"]
# pmlz_substrate = geom3D.subdomains_entities["volumes"]["pmlz_substrate"]

# pmlz_superstrate_sub = geom3D.subdomains["volumes"]["pmlz_superstrate"]
# pmlz_substrate_sub = geom3D.subdomains["volumes"]["pmlz_substrate"]


def get_geom_physical(geom3D):
    all_subdomains = list(geom3D.subdomains_entities["volumes"].values())
    all_subdomains_flat = [item for sublist in all_subdomains for item in sublist]
    lengths = [len(sublist) for sublist in all_subdomains]
    all_subdomains_name = list(geom3D.subdomains_entities["volumes"].keys())
    return all_subdomains_name, all_subdomains_flat, lengths


def restore_subs(geom3D, all_subdomains_name, all_subdomains_flat, lengths):
    i = 0
    all_subdomains_restored = []
    for n in lengths:
        all_subdomains_restored.append(all_subdomains_flat[i : i + n])
        i += n
    for name, num in zip(all_subdomains_name, all_subdomains_restored):
        geom3D.add_physical(num, name)
    return geom3D


mid_width = wg_width * 2
mid_thickness = wg_thickness * 3
mid_depth = wg_depth / 4

ysub = geom3D.y_position["superstrate"]

core = geom3D.add_box(
    -wg_width / 2,
    ysub,
    -geom3D.width[1] / 2,
    wg_width,
    wg_thickness,
    wg_depth,
)
mid = geom3D.add_box(
    -wg_width,
    ysub,
    -geom3D.width[1] / 2 + wg_depth,
    mid_width,
    mid_thickness,
    mid_depth,
)
end = geom3D.add_box(
    -wg_width / 2,
    ysub,
    -geom3D.width[1] / 2 + wg_depth + mid_depth,
    wg_width,
    wg_thickness,
    geom3D.width[1] - wg_depth - mid_depth,
)
all_subdomains_name, all_subdomains_flat, lengths = get_geom_physical(geom3D)
out = geom3D.fragment([core, mid, end], all_subdomains_flat)
core, mid, end, *all_subdomains_flat = out

geom3D = restore_subs(geom3D, all_subdomains_name, all_subdomains_flat, lengths)

geom3D.add_physical([core, end], "core")
geom3D.add_physical(mid, "mid")




# geom3D.add_physical(pmlz_core, "pmlz_core")


# # =========================
# # 2. Fragment all volumes at once
# # =========================
# new_entities, old_to_new_map_list = gmsh.model.occ.fragment(
#     all_subdomains_flat,
#     [],  # no tools needed; fragment all against each other
#     removeObject=False,
#     removeTool=False
# )
# gmsh.model.occ.synchronize()

# gmsh.model.occ.fragment(
#     geom3D.model.get_entities(2),
#     [],  # no tools needed; fragment all against each other
# )
# gmsh.model.occ.synchronize()


# # Convert old_to_new_map_list to a dict: old_tag -> [new_tags]
# old_to_new = {}
# for old_entry, new_list in zip(all_subdomains_flat, old_to_new_map_list):
#     old_tag = old_entry[1]
#     new_tags = [t[1] for t in new_list]
#     old_to_new[old_tag] = new_tags


# # gmsh.model.occ.removeAllDuplicates()
# # gmsh.model.occ.synchronize()

# # 4. Rebuild subdomains_entities with updated OCC tags
# # =========================
# new_subdomains_entities = {}
# for name, old_tags in geom3D.subdomains_entities["volumes"].items():
#     new_tags = []
#     for t in old_tags:
#         new_tags.extend(old_to_new.get(t, []))
#     new_subdomains_entities[name] = sorted(set(new_tags))


# # =========================
# # 5. Rebuild physical groups safely
# # =========================
# for name, occ_tags in new_subdomains_entities.items():
#     phys_tag = geom3D.subdomains["volumes"][name]
#     # remove old physical group if it exists
#     existing_groups = gmsh.model.getPhysicalGroupsForEntity(3, phys_tag)
#     # if existing_groups.tolist() != []:
#     gmsh.model.removePhysicalGroups([(3, phys_tag)])
#     gmsh.model.addPhysicalGroup(3, occ_tags, phys_tag)
#     gmsh.model.setPhysicalName(3, phys_tag, name)

# geom3D.set_size("superstrate", lmin / ncore)
# geom3D.set_size("substrate", lmin / ncore)
# geom3D.set_size("pmlz_core", lmin / ncore)
# geom3D.set_size("core", lmin / ncore)
print("Building 3D mesh")
geom3D.build(1)
print("Done 3D mesh")

xsxsx


def fragment_all(vols):
    """
    Fragment all volumes together in one call.
    vols: list of (dim, tag)
    Returns:
        new_entities: list of (dim, tag)
        full_map: dict mapping old tag -> list of new tags
    """
    # Keep all entities alive so mapping works
    new_entities, outMap = gmsh.model.occ.fragment(
        vols, [], removeObject=False, removeTool=False
    )
    gmsh.model.occ.synchronize()

    # Build full map: old_tag -> list of new_tags
    full_map = {}
    for old_list, new_list in zip(vols, outMap):
        old_tag = old_list[1]
        new_tags = [t[1] for t in new_list]
        full_map[old_tag] = new_tags

    return new_entities, full_map


new_entities, old_to_new = fragment_all(all_subdomains_flat)

new_subdomains_entities = {}

for name, old_tags in geom3D.subdomains_entities["volumes"].items():
    new_tags = []
    for t in old_tags:
        mapped = old_to_new.get(t, [])
        new_tags.extend(mapped)
    new_subdomains_entities[name] = sorted(set(new_tags))
for name, occ_tags in new_subdomains_entities.items():
    phys_tag = geom3D.subdomains["volumes"][name]
    # remove old group if it exists
    existing = gmsh.model.getPhysicalGroupsForEntity(3, phys_tag)
    if existing:
        gmsh.model.removePhysicalGroups([(3, phys_tag)])
    gmsh.model.addPhysicalGroup(3, occ_tags, phys_tag)
    gmsh.model.setPhysicalName(3, phys_tag, name)

# xsx
# new_entities, old_to_new = geom3D.fragment(all_subdomains_flat, [], map=True)
# def build_mapping(old_to_new_list):
#     mapping = {}
#     for (dim_old, old_tag), new_list in old_to_new_list:
#         mapping[(dim_old, old_tag)] = [new_tag for (_, new_tag) in new_list]
#     return mapping
# mapping = build_mapping(old_to_new)
# xsx
# # out = geom3D.fragment(core, [sup, sub,pmlz_substrate[1],pmlz_superstrate[1]])
# # core, sup, sub,pmlz_substrate,pmlz_superstrate = out

# out = geom3D.fragment([core] + all_subdomains_flat, [])
# core, *_ = out

# geom3D.add_physical(core, "core")
# # geom3D.add_physical(sub, "substrate")
# # geom3D.add_physical(sup, "superstrate")
# # geom3D.add_physical(pmlz_superstrate_new, "pmlz_superstrate")
# # geom3D.add_physical(pmlz_substrate_new, "pmlz_substrate")


# # # [geom3D.set_size(pml, lmin * 1) for pml in geom3D.pmls]
# # geom3D.set_size("superstrate", lmin / ncore)
# # geom3D.set_size("substrate", lmin / ncore)
# # # geom3D.set_size("pmlz_core", lmin / ncore)
# # # geom3D.set_size("core", lmin / ncore)

print("Building 3D mesh")
geom3D.build(1)
print("Done 3D mesh")

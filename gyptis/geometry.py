#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# License: MIT


"""
Geometry definition using Gmsh api.
For more information see Gmsh's `documentation <https://gmsh.info/doc/texinfo/gmsh.html>`_
"""

import numbers
import re
import sys
import tempfile
from functools import wraps

import gmsh
import numpy as np

from . import dolfin
from .measure import Measure
from .mesh import read_mesh

_geometry_module = sys.modules[__name__]

geo = gmsh.model.geo
occ = gmsh.model.occ
setnum = gmsh.option.setNumber

gmsh_options = gmsh.option

# def copy_docstring_from(source):
#     def wrapper(func):
#         func.__doc__ = source.__doc__
#         return func
#     return wrapper


def _set_opt_gmsh(name, value):
    if isinstance(value, str):
        return gmsh_options.setString(name, value)
    elif isinstance(value, numbers.Number) or isinstance(value, bool):
        if isinstance(value, bool):
            value = int(value)
        return gmsh_options.setNumber(name, value)
    else:
        raise ValueError("value must be string or number")


def _get_opt_gmsh(name):
    try:
        return gmsh_options.getNumber(name)
    except:
        return gmsh_options.getString(name)


setattr(gmsh_options, "set", _set_opt_gmsh)
setattr(gmsh_options, "get", _get_opt_gmsh)


def _add_method(cls, func, name):
    @wraps(func)
    def wrapper(*args, sync=True, **kwargs):
        out = func(*args, **kwargs)
        if sync:
            occ.synchronize()
        return out

    setattr(cls, name, wrapper)
    return func


def _dimtag(tag, dim=3):
    if not isinstance(tag, list):
        tag = list([tag])
    return [(dim, t) for t in tag]


def _get_bnd(id, dim):
    out = gmsh.model.getBoundary(_dimtag(id, dim=dim), False, False, False)
    return [b[1] for b in out]


def _convert_name(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _make_func(cls, name):
    class_name = getattr(_geometry_module, "_" + name)

    @wraps(class_name.__init__)
    def wrapper(self, *args, **kwargs):
        return class_name(cls, self, *args, **kwargs)

    setattr(cls, name, wrapper)
    # getattr(cls, name).__doc__ = class_name.__init__.__doc__
    return wrapper


class GeometryPrimitive(object):
    def __init__(
        self, geometry, add_function=None, id=-1, dim=2, name=None, physical_name=None
    ):
        self.geometry = geometry
        self.add_function = add_function
        self.id = id
        self.name = name
        self.dim = dim
        self._physical_name = physical_name
        # self.physical_name = physical_name

    def _get_geometry_method(self, m):
        return getattr(self.geometry, m)

    def _basic_operation(self, method, other):
        op = self._get_geometry_method(method)
        id = op(self.id, other.id)
        new = GeometryPrimitive(self.geometry)
        new.id = id
        return new

    def get_boundaries(self, physical=False):
        bnds = self._get_geometry_method("get_boundaries")(
            self.id, self.dim, physical=physical
        )
        new = [GeometryPrimitive(self.geometry, dim=self.dim - 1, id=id) for id in bnds]
        return new

    def add(self, *args, **kwargs):
        if self.add_function is not None:
            return self._get_geometry_method(self.add_function)(*args, **kwargs)

    def __len__(self):
        return len(self.id)

    def __add__(self, other):
        return self._basic_operation("fuse", other)

    def __sub__(self, other):
        return self._basic_operation("cut", other)

    @property
    def physical_name(self):
        return self._physical_name

    @physical_name.setter
    def physical_name(self, name):
        self.geometry.add_physical(self.id, name)
        self._physical_name = name

    def add_physical(self, name):
        self.physical_name = name

    def __lshift__(self, name):
        self.add_physical(name)

    def __truediv__(self, other):
        op = self._get_geometry_method("fragment")
        ids, map = op(self.id, other.id, map=True)
        new = []
        for id in ids:
            p = GeometryPrimitive(self.geometry)
            p.id = id
            new.append(p)
        return new

    def rotate(self, point, axis, angle):
        new = GeometryPrimitive(self.geometry)
        self._get_geometry_method("rotate")(self.id, point, axis, angle)
        new.id = self.id
        return new

    def extrude(self, vector, num_el=[], heights=[], recombine=False):
        new = GeometryPrimitive(self.geometry)
        dimtags = self.geometry.dimtag(self.id)

        self._get_geometry_method("extrude")(
            dimtags, *vector, num_el, heights, recombine
        )
        new.id = self.id
        new.dim = self.dim + 1
        return new

    def set_size(self, size, **kwargs):
        self.geometry.set_size(self.id, size, **kwargs)

    def __or__(self, size):
        return self.set_size(size)

    def __repr__(self):
        return f"GeometryPrimitive(id={self.id}, dim={self.dim})"

    # def __rshift__(self, other):
    #
    #     return _basic_operation("fragment", self, other)


class _Circle(GeometryPrimitive):
    def __init__(self, geometry, center, radius, surface=True, name=None, **kwargs):
        """
        Circle(center, radius, surface=True, name=None, **kwargs)

        Create and add a circle.

        Parameters
        ----------
        center : tuple
            Center (x,y,z).
        radius : float
            Radius.
        surface : bool
            Wether to create a plane surface (the default is True).
        name : str
            Name of the object (the default is None).

        Returns
        -------
        Circle
            A circle object.

        """
        super().__init__(geometry, "add_circle")
        self.radius = radius
        self.center = center
        self.surface = surface
        self.name = name
        self.add(**kwargs)

    def __repr__(self):
        return f"Circle(r={self.radius}, c={self.center})"

    def add(self, **kwargs):
        self.id = super().add(*self.center, self.radius, surface=self.surface, **kwargs)


class _Rectangle(GeometryPrimitive):
    def __init__(self, geometry, corner, size, corner_radius=0.0, name=None, **kwargs):
        """
        Rectangle(corner, size, corner_radius=0.0, name=None)

        Create and add a rectangle.

        Parameters
        ----------
        corner : tuple
            Corner (x,y,z).
        size : tuple
            Size (Lx, Ly).
        corner_radius : float
            Radius of corners (the default is 0.0).
        name : str
            Name of the object (the default is None).

        Returns
        -------
        Rectangle
            A rectangle object.

        """
        super().__init__(geometry, "add_rectangle")
        self.size = size
        self.corner = corner
        self.corner_radius = corner_radius
        self.name = name
        self.add(**kwargs)

    def add(self, **kwargs):
        self.id = super().add(
            *self.corner, *self.size, roundedRadius=self.corner_radius, **kwargs
        )


class _Ellipse(GeometryPrimitive):
    def __init__(self, geometry, center, radii, surface=True, name=None, **kwargs):
        """
        Ellipse(center, radii, surface=True, name=None, **kwargs)

        Create and add an ellipse.

        Parameters
        ----------
        center : tuple
            Center (x,y,z).
        radii : tuple
            Axes of the ellipse (Lx,Ly).
        surface : bool
            Wether to create a plane surface (the default is True).
        name : str
            Name of the object (the default is None).

        Returns
        -------
        Circle
            A circle object.

        """
        super().__init__(geometry, "add_ellipse")
        self.radii = radii
        self.center = center
        self.surface = surface
        self.name = name
        self.add(**kwargs)

    def __repr__(self):
        return f"Circle(r={self.radius}, c={self.center})"

    def add(self, **kwargs):
        self.id = super().add(*self.center, *self.radii, surface=self.surface, **kwargs)


class Geometry(object):
    """Base class for geometry models.

    Parameters
    ----------
    model_name : str
        Name of the model
    mesh_name : str
        Name of the mesh file (.msh).
    data_dir : str
        Directory to store generated mesh and data.
    dim : int
        Dimension of the problem.

    Attributes
    ----------
    subdomains : dict
        Dictionary containing mapping from physical domains names to their
        index.
    model_name
    mesh_name
    dim
    data_dir

    """

    def __init__(
        self,
        model_name="geometry",
        mesh_name="mesh.msh",
        data_dir=None,
        dim=3,
        gmsh_args=None,
        kill=True,
        options={},
    ):
        self.model_name = model_name
        self.mesh_name = mesh_name
        self.dim = dim
        self.subdomains = dict(volumes={}, surfaces={}, curves={}, points={})
        self.data_dir = data_dir if data_dir else tempfile.mkdtemp()
        self.occ = occ
        self.mesh_object = {}
        self.measure = {}
        self.mesh = {}
        self.markers = {}
        self.options = options

        for object_name in dir(occ):
            if (
                not object_name.startswith("__")
                and object_name != "mesh"
                and object_name not in dir(self)
            ):
                bound_method = getattr(occ, object_name)
                name = _convert_name(bound_method.__name__)
                _add_method(self, bound_method, name)

        self._gmsh_add_ellipse = self.add_ellipse
        del self.add_ellipse
        self._gmsh_add_circle = self.add_circle
        del self.add_circle
        self._gmsh_add_spline = self.add_spline
        del self.add_spline

        if kill:
            try:
                gmsh.finalize()
            except:
                pass

        self.gmsh_args = gmsh_args
        if gmsh_args is not None:
            gmsh.initialize(self.gmsh_args)
        else:
            gmsh.initialize()
        #

        # parallel meshing, this will use OMP_NUM_THREADS
        for k, v in options.items():
            gmsh_options.set(k, v)

        # gmsh_options.set("General.Verbosity", 0)

    @wraps(_Circle.__init__)
    def Circle(self, *args, **kwargs):
        return _Circle(self, *args, **kwargs)

    @wraps(_Rectangle.__init__)
    def Rectangle(self, *args, **kwargs):
        return _Rectangle(self, *args, **kwargs)

    @wraps(_Ellipse.__init__)
    def Ellipse(self, *args, **kwargs):
        return _Ellipse(self, *args, **kwargs)

    # def add_rectangle(self, *args, **kwargs):
    #     return self.add_rectangle(*args, **kwargs)

    def rotate(self, tag, point, axis, angle, dim=None):
        dt = self.dimtag(tag, dim=dim)
        return occ.rotate(dt, *point, *axis, angle)

    def add_physical(self, id, name, dim=None):
        """Add a physical domain.

        Parameters
        ----------
        id : int or list of int
            The identifiant(s) of elementary entities making the physical domain.
        name : str
            Name of the domain.
        dim : int
            Dimension.
        """
        dim = dim if dim else self.dim
        dicname = list(self.subdomains)[3 - dim]
        if not isinstance(id, list):
            id = list([id])
        num = gmsh.model.addPhysicalGroup(dim, id)
        self.subdomains[dicname][name] = num
        gmsh.model.removePhysicalName(name)
        gmsh.model.setPhysicalName(dim, self.subdomains[dicname][name], name)
        return num

    def dimtag(self, id, dim=None):
        """Convert an integer or list of integer to gmsh DimTag notation.

        Parameters
        ----------
        id : int or list of int
            Label or list of labels.
        dim : type
            Dimension.

        Returns
        -------
        int or list of int
            A tuple (dim, tag) or list of such tuples (gmsh DimTag notation).

        """
        dim = dim or self.dim
        return _dimtag(id, dim=dim)

    # def add_circle(self,x, y, z, ax, ay,**kwargs):
    #     ell = self._gmsh_add_ellipse(x, y, z, ax, ay,**kwargs)
    #     ell = self.add_curve_loop([ell])
    #     return self.add_plane_surface([ell])

    def add_circle(self, x, y, z, r, surface=True, **kwargs):
        if surface:
            circ = self._gmsh_add_circle(x, y, z, r, **kwargs)
            circ = self.add_curve_loop([circ])
            return self.add_plane_surface([circ])
        else:
            return self._gmsh_add_circle(x, y, z, r, **kwargs)

    def add_ellipse(self, x, y, z, ax, ay, surface=True, **kwargs):
        if ax == ay:
            return self.add_circle(x, y, z, ax, surface=surface, **kwargs)
        elif ax < ay:
            ell = self.add_ellipse(x, y, z, ay, ax, surface=surface, **kwargs)
            self.rotate(ell, (x, y, z), (0, 0, 1), np.pi / 2, dim=2)
            return ell
        else:
            if surface:
                ell = self._gmsh_add_ellipse(x, y, z, ax, ay, **kwargs)
                ell = self.add_curve_loop([ell])
                return self.add_plane_surface([ell])
            else:
                return self._gmsh_add_ellipse(x, y, z, ax, ay, **kwargs)

    def add_spline(self, points, mesh_size=0.0, surface=True, **kwargs):
        """Adds a spline.

        Parameters
        ----------
        points : array of shape (Npoints,3)
            Corrdinates of the points.
        mesh_size : float
            Mesh sizes at points (the default is 0.0).
        surface : type
            If True, creates a plane surface (the default is True).

        Returns
        -------
        int
            The tag of the spline.

        """
        dt = []
        for p in points:
            dt.append(self.add_point(*p, meshSize=mesh_size))

        if np.allclose(points[0], points[-1]):
            dt[-1] = dt[0]

        if surface:
            spl = self._gmsh_add_spline(dt, **kwargs)
            spl = self.add_curve_loop([spl])
            return self.add_plane_surface([spl])
        else:
            return self._gmsh_add_spline(dt, **kwargs)

    def fragment(self, id1, id2, dim1=None, dim2=None, sync=True, map=False, **kwargs):
        dim1 = dim1 if dim1 else self.dim
        dim2 = dim2 if dim2 else self.dim
        a1 = self.dimtag(id1, dim1)
        a2 = self.dimtag(id2, dim2)
        dimtags, mapping = occ.fragment(a1, a2, **kwargs)
        if sync:
            occ.synchronize()
        tags = [_[1] for _ in dimtags]
        if map:
            return tags, mapping
        else:
            return tags

    def cut(self, id1, id2, dim1=None, dim2=None, sync=True, **kwargs):
        dim1 = dim1 if dim1 else self.dim
        dim2 = dim2 if dim2 else self.dim
        a1 = self.dimtag(id1, dim1)
        a2 = self.dimtag(id2, dim2)
        ov, ovv = occ.cut(a1, a2, **kwargs)
        if sync:
            occ.synchronize()
        return [o[1] for o in ov]

    def fuse(self, id1, id2, dim1=None, dim2=None, sync=True):
        dim1 = dim1 if dim1 else self.dim
        dim2 = dim2 if dim2 else self.dim
        a1 = self.dimtag(id1, dim1)
        a2 = self.dimtag(id2, dim2)
        ov, ovv = occ.fuse(a1, a2)
        if sync:
            occ.synchronize()
        return [o[1] for o in ov]

    def get_boundaries(self, id, dim=None, physical=True):
        dim = dim if dim else self.dim
        if isinstance(id, str):
            if dim == 3:
                type_entity = "volumes"
            elif dim == 2:
                type_entity = "surfaces"
            else:
                type_entity = "curves"
            id = self.subdomains[type_entity][id]

            n = gmsh.model.getEntitiesForPhysicalGroup(dim, id)
            bnds = [_get_bnd(n_, dim=dim) for n_ in n]
            bnds = [item for sublist in bnds for item in sublist]
            return list(dict.fromkeys(bnds))
        else:
            if physical:
                n = gmsh.model.getEntitiesForPhysicalGroup(dim, id)[0]
            else:
                n = id
            return _get_bnd(n, dim=dim)

    def _set_size(self, id, s, dim=None):
        dim = dim if dim else self.dim
        p = gmsh.model.getBoundary(
            self.dimtag(id, dim=dim), False, False, True
        )  # Get all points
        gmsh.model.mesh.setSize(p, s)

    def _check_subdomains(self):
        groups = gmsh.model.getPhysicalGroups()
        names = [gmsh.model.getPhysicalName(*g) for g in groups]
        for subtype, subitems in self.subdomains.items():
            for id in subitems.copy().keys():
                if id not in names:
                    subitems.pop(id)

    def set_mesh_size(self, params, dim=None):
        dim = dim if dim else self.dim
        if dim == 3:
            type_entity = "volumes"
        elif dim == 2:
            type_entity = "surfaces"
        elif dim == 1:
            type_entity = "curves"
        elif dim == 0:
            type_entity = "points"

        # revert sort so that smaller sizes are set last
        params = dict(
            sorted(params.items(), key=lambda item: float(item[1]), reverse=True)
        )

        for id, p in params.items():
            if isinstance(id, str):
                num = self.subdomains[type_entity][id]
                n = gmsh.model.getEntitiesForPhysicalGroup(dim, num)
                for n_ in n:
                    self._set_size(n_, p, dim=dim)
            else:
                self._set_size(id, p, dim=dim)

    def set_size(self, id, s, dim=None):
        if hasattr(id, "__len__") and not isinstance(id, str):
            for i, id_ in enumerate(id):
                if hasattr(s, "__len__"):
                    s_ = s[i]
                else:
                    s_ = s
                params = {id_: s_}
                self.set_mesh_size(params, dim=dim)
        else:
            self.set_mesh_size({id: s}, dim=dim)

    def read_mesh_info(self):
        if self.dim == 2:
            marker_dim = "triangle"
            sub_dim = "surfaces"
            marker_dim_minus_1 = "line"
            sub_dim_dim_minus_1 = "curves"
        else:
            marker_dim = "tetra"
            sub_dim = "volumes"
            marker_dim_minus_1 = "triangle"
            sub_dim_dim_minus_1 = "surfaces"

        self.measure["dx"] = Measure(
            "dx",
            domain=self.mesh_object["mesh"],
            subdomain_data=self.mesh_object["markers"][marker_dim],
            subdomain_dict=self.subdomains[sub_dim],
        )

        # exterior_facets
        if (marker_dim_minus_1 in self.mesh_object["markers"].keys()) and (
            sub_dim_dim_minus_1 in self.subdomains.keys()
        ):
            self.measure["ds"] = Measure(
                "ds",
                domain=self.mesh_object["mesh"],
                subdomain_data=self.mesh_object["markers"][marker_dim_minus_1],
                subdomain_dict=self.subdomains[sub_dim_dim_minus_1],
            )

            # interior_facets

            self.measure["dS"] = Measure(
                "dS",
                domain=self.mesh_object["mesh"],
                subdomain_data=self.mesh_object["markers"][marker_dim_minus_1],
                subdomain_dict=self.subdomains[sub_dim_dim_minus_1],
            )
        else:
            self.measure["ds"] = None
            self.measure["dS"] = None

        self.mesh = self.mesh_object["mesh"]
        self.markers = self.mesh_object["markers"]

        if self.dim == 2:
            self.domains = self.subdomains["surfaces"]
            self.boundaries = self.subdomains["curves"]
            self.lines = {}
            self.points = self.subdomains["points"]
            self.markers = self.mesh_object["markers"]["triangle"]
            self.boundary_markers = (
                self.mesh_object["markers"]["line"] if self.boundaries else []
            )

        else:
            self.domains = self.subdomains["volumes"]
            self.boundaries = self.subdomains["surfaces"]
            self.lines = self.subdomains["curves"]
            self.points = self.subdomains["points"]
            self.markers = self.mesh_object["markers"]["tetra"]
            self.boundary_markers = (
                self.mesh_object["markers"]["triangle"] if self.boundaries else []
            )

        self.unit_normal_vector = dolfin.FacetNormal(self.mesh)

    @property
    def msh_file(self):
        return f"{self.data_dir}/{self.mesh_name}"

    def build(
        self,
        interactive=False,
        generate_mesh=True,
        write_mesh=True,
        read_info=True,
        read_mesh=True,
        finalize=True,
        check_subdomains=True,
    ):
        if check_subdomains:
            self._check_subdomains()

        self.mesh_object = self.generate_mesh(
            generate=generate_mesh, write=write_mesh, read=read_mesh
        )

        if read_info:
            self.read_mesh_info()

        if interactive:
            gmsh.fltk.run()
        if finalize:
            gmsh.finalize()
        return self.mesh_object

    def read_mesh_file(self):
        return read_mesh(self.msh_file, data_dir=self.data_dir, dim=self.dim)

    def generate_mesh(self, generate=True, write=True, read=True):
        if generate:
            gmsh.model.mesh.generate(self.dim)
        if write:
            gmsh.write(self.msh_file)
        if read:
            return self.read_mesh_file()

    def plot_mesh(self, **kwargs):
        return dolfin.plot(self.mesh, **kwargs)

    def plot_subdomains(self, **kwargs):
        from .plot import plot_subdomains

        return plot_subdomains(self.markers, **kwargs)

    def add(self, primittive):
        primittive.add(self)
        ids = []
        for p in primittive.parents:
            self.add(p)
            ids.append(p.id)
        for op in primittive.operations:
            IDs = op(self, *ids)
            primittive.id = IDs

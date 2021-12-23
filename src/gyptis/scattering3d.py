#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# License: MIT


from . import dolfin
from . import spharm as sh
from .complex import *
from .formulation import Maxwell3D
from .geometry import *
from .materials import *
from .simulation import Simulation
from .source import *
from .utils._meta import _ScatteringBase


class BoxPML3D(Geometry):
    def __init__(
        self,
        box_size=(1, 1, 1),
        box_center=(0, 0, 0),
        pml_width=(0.2, 0.2, 0.2),
        Rcalc=0,
        **kwargs,
    ):
        super().__init__(
            dim=3,
            **kwargs,
        )
        self.box_size = box_size
        self.box_center = box_center
        self.pml_width = pml_width
        self.Rcalc = Rcalc

        box = self._addbox_center(self.box_size)
        T = np.array(self.pml_width) / 2 + np.array(self.box_size) / 2

        s = (self.pml_width[0], self.box_size[1], self.box_size[2])
        t = np.array([T[0], 0, 0])
        pmlxp = self._add_pml(s, t)
        pmlxm = self._add_pml(s, -t)

        s = (self.box_size[0], self.pml_width[1], self.box_size[2])
        t = np.array([0, T[1], 0])
        pmlyp = self._add_pml(s, t)
        pmlym = self._add_pml(s, -t)

        s = (self.box_size[0], self.box_size[1], self.pml_width[2])
        t = np.array([0, 0, T[2]])
        pmlzp = self._add_pml(s, t)
        pmlzm = self._add_pml(s, -t)

        s = (self.pml_width[0], self.pml_width[1], self.box_size[2])
        pmlxypp = self._add_pml(s, [T[0], T[1], 0])
        pmlxypm = self._add_pml(s, [T[0], -T[1], 0])
        pmlxymp = self._add_pml(s, [-T[0], T[1], 0])
        pmlxymm = self._add_pml(s, [-T[0], -T[1], 0])

        s = (self.box_size[0], self.pml_width[1], self.pml_width[2])
        pmlyzpp = self._add_pml(s, [0, T[1], T[2]])
        pmlyzpm = self._add_pml(s, [0, T[1], -T[2]])
        pmlyzmp = self._add_pml(s, [0, -T[1], T[2]])
        pmlyzmm = self._add_pml(s, [0, -T[1], -T[2]])

        s = (self.pml_width[0], self.box_size[1], self.pml_width[2])
        pmlxzpp = self._add_pml(s, [T[0], 0, T[2]])
        pmlxzpm = self._add_pml(s, [T[0], 0, -T[2]])
        pmlxzmp = self._add_pml(s, [-T[0], 0, T[2]])
        pmlxzmm = self._add_pml(s, [-T[0], 0, -T[2]])

        s = (self.pml_width[0], self.pml_width[1], self.pml_width[2])
        pmlxyzppp = self._add_pml(s, [T[0], T[1], T[2]])
        pmlxyzppm = self._add_pml(s, [T[0], T[1], -T[2]])
        pmlxyzpmp = self._add_pml(s, [T[0], -T[1], T[2]])
        pmlxyzpmm = self._add_pml(s, [T[0], -T[1], -T[2]])
        pmlxyzmpp = self._add_pml(s, [-T[0], T[1], T[2]])
        pmlxyzmpm = self._add_pml(s, [-T[0], T[1], -T[2]])
        pmlxyzmmp = self._add_pml(s, [-T[0], -T[1], T[2]])
        pmlxyzmmm = self._add_pml(s, [-T[0], -T[1], -T[2]])

        pmlx = [pmlxp, pmlxm]
        pmly = [pmlyp, pmlym]
        pmlz = [pmlzp, pmlzm]
        pml1 = pmlx + pmly + pmlz

        pmlxy = [pmlxypp, pmlxypm, pmlxymp, pmlxymm]
        pmlyz = [pmlyzpp, pmlyzpm, pmlyzmp, pmlyzmm]
        pmlxz = [pmlxzpp, pmlxzpm, pmlxzmp, pmlxzmm]
        pml2 = pmlxy + pmlyz + pmlxz

        pml3 = [
            pmlxyzppp,
            pmlxyzppm,
            pmlxyzpmp,
            pmlxyzpmm,
            pmlxyzmpp,
            pmlxyzmpm,
            pmlxyzmmp,
            pmlxyzmmm,
        ]

        self.box = box
        self.pmls = pml1 + pml2 + pml3
        self._translate([self.box] + self.pmls, self.box_center)
        self.fragment(self.box, self.pmls)

        if Rcalc > 0:
            sphere_calc = self.add_sphere(*self.box_center, Rcalc)
            box, sphere_calc = self.fragment(box, sphere_calc)
            self.box = [box, sphere_calc]

        self.add_physical(box, "box")
        self.add_physical(pmlx, "pmlx")
        self.add_physical(pmly, "pmly")
        self.add_physical(pmlz, "pmlz")
        self.add_physical(pmlxy, "pmlxy")
        self.add_physical(pmlyz, "pmlyz")
        self.add_physical(pmlxz, "pmlxz")
        self.add_physical(pml3, "pmlxyz")

        self.pml_physical = [
            "pmlx",
            "pmly",
            "pmlz",
            "pmlxy",
            "pmlyz",
            "pmlxz",
            "pmlxyz",
        ]

        if Rcalc > 0:
            bnds = self.get_boundaries("box")
            self.calc_bnds = bnds[0]
            self.add_physical(self.calc_bnds, "calc_bnds", dim=2)

    def _addbox_center(self, rect_size):
        corner = -np.array(rect_size) / 2
        corner = tuple(corner)
        return self.add_box(*corner, *rect_size)

    def _translate(self, tag, t):
        translation = tuple(t)
        self.translate(self.dimtag(tag), *translation)

    def _add_pml(self, s, t):
        pml = self._addbox_center(s)
        self._translate(pml, t)
        return pml


class Scatt3D(_ScatteringBase, Simulation):
    def __init__(
        self,
        geometry,
        epsilon,
        mu,
        source=None,
        boundary_conditions={},
        polarization=None,
        modal=False,
        degree=1,
        pml_stretch=1 - 1j,
        element="N1curl",
    ):
        assert isinstance(geometry, BoxPML3D)
        assert source.dim == 3
        function_space = ComplexFunctionSpace(geometry.mesh, element, degree)
        pmls = []
        pml_names = []
        for direction in ["x", "y", "z", "xy", "yz", "xz", "xyz"]:
            pml_name = f"pml{direction}"
            pml_names.append(pml_name)
            pmls.append(
                PML(
                    direction,
                    stretch=pml_stretch,
                    matched_domain="box",
                    applied_domain=pml_name,
                )
            )

        epsilon_coeff = Coefficient(
            epsilon,
            geometry,
            pmls=pmls,
            degree=degree,
            dim=3,
        )
        mu_coeff = Coefficient(
            mu,
            geometry,
            pmls=pmls,
            degree=degree,
            dim=3,
        )

        coefficients = epsilon_coeff, mu_coeff
        no_source_domains = ["box"] + pml_names
        source_domains = [
            dom for dom in geometry.domains if dom not in no_source_domains
        ]

        formulation = Maxwell3D(
            geometry,
            coefficients,
            function_space,
            source=source,
            source_domains=source_domains,
            reference="box",
            boundary_conditions=boundary_conditions,
        )

        super().__init__(geometry, formulation)

        self.Z0 = np.sqrt(mu_0 / epsilon_0)
        self.S0 = 1 / (2 * self.Z0)
        self.degree = degree

    def solve_system(self, again=False):
        E = super().solve_system(again=again, vector_function=False)
        self.solution = {}
        self.solution["diffracted"] = E
        self.solution["total"] = E + self.source.expression
        return E

    def _cross_section_helper(self, return_type="s", boundaries="calc_bnds"):

        parallel = dolfin.MPI.comm_world.size > 1
        ### normal vector is messing up in parallel so workaround here:
        if parallel:
            Rcalc = self.geometry.Rcalc
            n_out = dolfin.Expression(
                (f"-x[0]/{Rcalc}", f"-x[1]/{Rcalc}", f"-x[2]/{Rcalc}"),
                degree=self.degree,
            )
        else:
            n_out = self.geometry.unit_normal_vector

        Es = self.solution["diffracted"]
        omega = self.source.pulsation
        inv_mu_coeff = self.formulation.mu.invert().as_subdomain()
        Hs = inv_mu_coeff / Complex(0, dolfin.Constant(omega * mu_0)) * curl(Es)
        Ss = dolfin.Constant(0.5) * cross(Es, Hs.conj).real

        Ei = self.source.expression
        mu_a = self.formulation.mu.build_annex(
            domains=self.formulation.source_domains,
            reference=self.formulation.reference,
        )
        inv_mua_coeff = mu_a.invert().as_subdomain()
        Hi = inv_mua_coeff / Complex(0, dolfin.Constant(omega * mu_0)) * curl(Ei)
        Si = dolfin.Constant(0.5) * cross(Ei, Hi.conj).real
        Se = dolfin.Constant(0.5) * (cross(Ei, Hs.conj) + cross(Es, Hi.conj)).real

        Etot = self.solution["total"]
        Htot = inv_mu_coeff / Complex(0, dolfin.Constant(omega * mu_0)) * curl(Etot)
        Stot = dolfin.Constant(0.5) * cross(Etot, Htot.conj).real

        if return_type == "s":
            Ws = assemble(dot(n_out("+"), Ss("+")) * self.dS(boundaries))
            Sigma_s = Ws / self.S0
            return Sigma_s

        if return_type == "e":
            We = -assemble(dot(n_out("+"), Se("+")) * self.dS(boundaries))
            Sigma_e = We / self.S0
            return Sigma_e

        if return_type == "a":
            Wa = -assemble(dot(n_out("+"), Stot("+")) * self.dS(boundaries))
            Sigma_a = Wa / self.S0
            return Sigma_a

    def scattering_cross_section(self, **kwargs):
        return self._cross_section_helper("s", **kwargs)

    def extinction_cross_section(self, **kwargs):
        return self._cross_section_helper("e", **kwargs)

    def absorption_cross_section(self, **kwargs):
        return self._cross_section_helper("a", **kwargs)

    def get_T_matrix_coeff(
        self,
        p0,
        p1,
        source_type,
        coeff_type,
        solve_again=False,
        degree_source=None,
        component="transverse",
        boundary="calc_bnds",
    ):
        if coeff_type not in ["E", "H", "both"]:
            raise ValueError("coeff_type must be E, H or both")
        if component not in ["normal", "transverse"]:
            raise ValueError("component must be either normal or transverse")
        degree_source = degree_source or self.degree
        Rcalc = self.geometry.Rcalc
        wavelength = self.source.wavelength
        n0, m0 = sh.p2nm(p0)
        n1, m1 = sh.p2nm(p1)
        mesh = self.geometry.mesh
        if source_type == "N":
            source = sh.SphericalN(
                wavelength,
                n0,
                m0,
                domain=mesh,
                degree=degree_source,
            )
        else:
            source = sh.SphericalM(
                wavelength,
                n0,
                m0,
                domain=mesh,
                degree=degree_source,
            )

        self.source = source

        if not solve_again:
            self.solve()
        else:
            self.assemble_rhs()
            self.solve_system(again=solve_again)

        Escat = self.solution["diffracted"]
        k = source.wavenumber

        def _postpro_coeff_e():
            if component == "normal":
                # normal components
                Y = sh.SphericalY(
                    wavelength,
                    n1,
                    m1,
                    domain=mesh,
                    degree=degree_source,
                )
                integrand = dot(Escat, Y.expression.conj)
                I = assemble(
                    0.5 * (integrand("+")) * self.dS(boundary) + Constant(0) * self.dx
                ) / (Rcalc ** 2)
                coeff = (
                    I * k * Rcalc / (sh.sph_hn2(n1, k * Rcalc) * (n1 * (n1 + 1)) ** 0.5)
                )
            else:
                # transverse components
                Z = sh.SphericalZ(
                    wavelength,
                    n1,
                    m1,
                    domain=mesh,
                    degree=degree_source,
                )
                integrand = dot(Escat, Z.expression.conj)
                I = assemble(
                    0.5 * (integrand("+")) * self.dS(boundary) + Constant(0) * self.dx
                ) / (Rcalc ** 2)
                xsi_prime = sh.rb_hn2(n1 - 1, k * Rcalc) - n1 * sh.sph_hn2(
                    n1, k * Rcalc
                )
                coeff = I * k * Rcalc / xsi_prime
            return coeff

        def _postpro_coeff_h():
            X = sh.SphericalX(
                wavelength,
                n1,
                m1,
                domain=mesh,
                degree=degree_source,
            )
            integrand = dot(Escat, X.expression.conj)
            I = (
                assemble(
                    0.5 * (integrand("+")) * self.dS(boundary) + Constant(0) * self.dx
                )
                / Rcalc ** 2
            )
            coeff = I / (sh.sph_hn2(n1, k * Rcalc))
            return coeff

        if coeff_type == "E":
            return _postpro_coeff_e()
        elif coeff_type == "H":
            return _postpro_coeff_h()
        elif coeff_type == "both":
            return _postpro_coeff_e(), _postpro_coeff_h()

    def get_T_matrix(
        self,
        p_max,
        degree_source=None,
        component="transverse",
        boundary="calc_bnds",
    ):

        T11 = np.zeros((p_max, p_max)).tolist()
        T21 = np.zeros((p_max, p_max)).tolist()
        T12 = np.zeros((p_max, p_max)).tolist()
        T22 = np.zeros((p_max, p_max)).tolist()

        solve_again = False
        for p0 in range(1, p_max + 1):
            for p1 in range(1, p_max + 1):
                for source_type in ["M", "N"]:
                    fe, fh = self.get_T_matrix_coeff(
                        p0,
                        p1,
                        source_type,
                        coeff_type="both",
                        solve_again=solve_again,
                        degree_source=degree_source,
                        component=component,
                        boundary=boundary,
                    )
                    solve_again = True

                    if source_type == "M":
                        T11[p0 - 1][p1 - 1] = fh
                        T21[p0 - 1][p1 - 1] = fe
                    else:
                        T12[p0 - 1][p1 - 1] = fh
                        T22[p0 - 1][p1 - 1] = fe

        Tmatrix = [[T11, T12], [T21, T22]]
        return Tmatrix
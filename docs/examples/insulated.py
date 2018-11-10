"""

Steady conduction with generation in an insulated wire

Carslaw, H. S., & J. C. Jaeger (1959). _Conduction of Heat in Solids_ 
(2nd ed.). Oxford University Press. §7.2.V, pp 191–192

∇ ⋅ (k0 ∇ T) + A = 0 in 0 < r < a

and 

∇ ⋅ (k1 ∇ T) = 0 in a < r < b

with k1 ∂T/∂r + h T = 0 on r = b.

"""

from functools import partial
from typing import Optional

import numpy as np

import meshio
from pygmsh import generate_mesh
from pygmsh.built_in import Geometry

from skfem.assembly import (InteriorBasis, FacetBasis,
                            bilinear_form, linear_form, asm)
from skfem.element import ElementTriP1
from skfem.mesh import MeshTri
from skfem.models.poisson import mass
from skfem.utils import solve

radii = [2., 3.]
joule_heating = 5.
heat_transfer_coefficient = 7.
thermal_conductivity = np.array([101.,  11.])


def make_mesh(a: float,         # radius of wire
              b: float,         # radius of insulation
              dx: Optional[float] = None) -> MeshTri:
    
    dx = a / 2 ** 3 if dx is None else dx

    origin = np.zeros(3)
    geom = Geometry()
    wire = geom.add_circle(origin, a, dx, make_surface=True)
    geom.add_physical_surface(wire.plane_surface, 'wire')
    insulation = geom.add_circle(origin, b, dx, holes=[wire.line_loop])
    geom.add_physical_surface(insulation.plane_surface, 'insulation')
    geom.add_physical_line(insulation.line_loop.lines, 'convection')

    return MeshTri.from_meshio(meshio.Mesh(*generate_mesh(geom)))

    return mesh

mesh = make_mesh(*radii)
regions = mesh.external.cell_data['triangle']['gmsh:physical'] - 1

@bilinear_form
def conduction(u, du, v, dv, w):
    return w.w * sum(du * dv)

convection = mass

element = ElementTriP1()
basis = InteriorBasis(mesh, element)


def elemental(x: np.ndarray) -> np.ndarray:
    return np.tile(x, (len(basis.W), 1)).T


L = asm(conduction, basis, w=elemental(thermal_conductivity[regions]))

facet_basis = FacetBasis(mesh, element, facets=mesh.boundaries['convection'])
H = heat_transfer_coefficient * asm(convection, facet_basis)


@linear_form
def generation(v, dv, w):
    return w.w * v

f = joule_heating * asm(generation, basis, w=elemental(regions == 0))

temperature = solve(L + H, f)

if __name__ == '__main__':

    from os.path import splitext
    from sys import argv
    

    T0 = {'skfem': basis.interpolator(temperature)(np.zeros((2, 1)))[0],
          'exact':
          (joule_heating * radii[0]**2 / 4 / thermal_conductivity[0] *
           (2 * thermal_conductivity[0] / heat_transfer_coefficient / radii[1]
            + (2 * thermal_conductivity[0] / thermal_conductivity[1]
               * np.log(radii[1] /radii[0])) + 1))}
    print('Central temperature:', T0)
    
    ax = mesh.plot(temperature)
    ax.axis('off')
    fig = ax.get_figure()
    fig.colorbar(ax.get_children()[0])
    fig.savefig(splitext(argv[0])[0] + '.png')
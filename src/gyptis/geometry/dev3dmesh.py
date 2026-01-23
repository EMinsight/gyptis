#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# License: GPLv3


import gmsh

gmsh.initialize()

# Create geometries
box1 = gmsh.model.occ.addBox(0, 0, 0, 1, 1, 1)
box2 = gmsh.model.occ.addBox(0.5, 0, 0, 0.1, 0.1, 0.1)
# sphere = gmsh.model.occ.addSphere(1.5, 0.5, 0.5, 0.3)

# Fragment preserves mapping
all_vols = [(3, box1), (3, box2)]
out, out_map = gmsh.model.occ.fragment(all_vols, [])

gmsh.model.occ.synchronize()

# Assign physical groups based on out_map
names = ["box1", "box2"]

print("\nFragment results (out_map):")
for i, entities in enumerate(out_map):
    print(f"  {names[i]}: {entities}")

# # Strategy 1: Each original geometry gets its fragments (may overlap)
# for i, entities in enumerate(out_map):
#     if entities:
#         tags = [e[1] for e in entities]
#         phys_tag = i + 1
#         gmsh.model.addPhysicalGroup(3, tags, phys_tag)
#         gmsh.model.setPhysicalName(3, phys_tag, names[i])

# Strategy 2 (commented): Assign unique regions only
# Find which volumes appear in multiple out_map entries
all_tags = [e[1] for entities in out_map for e in entities]
unique_tags = [tag for tag in all_tags if all_tags.count(tag) == 1]
shared_tags = list(set([tag for tag in all_tags if all_tags.count(tag) > 1]))

for i, entities in enumerate(out_map):
    tags = [e[1] for e in entities if e[1] in unique_tags]
    if tags:
        gmsh.model.addPhysicalGroup(3, tags, i+1)
        gmsh.model.setPhysicalName(3, i+1, names[i])

if shared_tags:
    gmsh.model.addPhysicalGroup(3, shared_tags, 999)
    gmsh.model.setPhysicalName(3, 999, "overlap")

# Generate mesh
gmsh.model.mesh.generate(3)

# Show physical groups in GUI:
# Tools → Options → Mesh → Surface faces/Volume faces → Color by physical group
print("\nPhysical groups assigned:")
for i, name in enumerate(names):
    print(f"  {name} → Physical Volume {i+1}")

gmsh.fltk.run()
gmsh.finalize()
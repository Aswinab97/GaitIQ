import trimesh

s = trimesh.load("prosthetic_leg.glb", force="scene")
print("Geometry count:", len(s.geometry))
print("Graph nodes:", len(s.graph.nodes_geometry))

# Show full scene with original transforms
s.show()
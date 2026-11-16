"""Render a preview PNG from the generated models: python render_preview.py models assets/preview.png [design]"""
import sys, os
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

d, out = sys.argv[1], sys.argv[2]
dz = sys.argv[3] if len(sys.argv) > 3 else "cloud"
parts = [(trimesh.load(os.path.join(d, f"{dz}_trophy_base.stl")), (0.13, 0.17, 0.24)),
         (trimesh.load(os.path.join(d, f"_{dz}_symbol_assembled.stl")), (1.0, 0.6, 0.0)),
         (trimesh.load(os.path.join(d, f"{dz}_trophy_label_inlay.stl")), (1.0, 0.6, 0.0))]
light = np.array([0.4, -0.7, 0.9]); light /= np.linalg.norm(light)
fig = plt.figure(figsize=(15, 5.2), dpi=110)
for i, (elev, azim) in enumerate([(22, -60), (8, -90), (35, -20)]):
    ax = fig.add_subplot(1, 3, i + 1, projection="3d")
    tris = np.vstack([m.triangles for m, _ in parts])        # one collection -> per-face depth sort
    cols = np.vstack([np.outer(0.45 + 0.55 * np.clip(m.face_normals @ light, 0, 1), c) for m, c in parts])
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols.clip(0, 1), edgecolor="none"))
    ax.set_xlim(-64, 64); ax.set_ylim(-40, 40); ax.set_zlim(0, 95)
    ax.set_box_aspect((128, 80, 95), zoom=1.25); ax.view_init(elev, azim); ax.set_axis_off()
plt.subplots_adjust(0, 0, 1, 1, 0, 0)
os.makedirs(os.path.dirname(out), exist_ok=True)
plt.savefig(out, facecolor="white")

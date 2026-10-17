import math, os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import soporte as s

OUT = os.path.join(os.path.dirname(__file__), "out")
VERDE = "#1D9E75"; AZUL = "#378ADD"; MADERA = "#E3B26A"; MADERA_B = "#9A6A2A"


def mesh_of(m):
    mm = m.to_mesh()
    t = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts)
    t.merge_vertices()
    return t


def bottle_outline(h, d, base_t=0.0, neck_d=28.0):
    """Silueta 2D (XZ) de una botella simple, en coordenadas del mueble."""
    r, rn = d / 2, neck_d / 2
    shoulder = h * 0.68
    neck0 = h * 0.86
    local = [(-r, 0), (r, 0), (r, shoulder), (rn, neck0), (rn, h), (-rn, h), (-rn, neck0), (-r, shoulder)]
    pts = []
    for x, z in local:
        p = s.B + (base_t + z) * s.U + x * s.N
        pts.append((p[0], p[2]))
    return pts


def side_view():
    principal = mesh_of(s.soporte_principal())
    fig, axes = plt.subplots(1, 3, figsize=(15, 7.2), sharey=True)
    casos = [("1,5 L", 320, 90, 0.0, None),
             ("1 L (suplemento A + reductor)", 258, 83, 55.0, "A"),
             ("500 ml (suplementos A + B + reductor)", 220, 68, 90.0, "AB")]
    for ax, (nombre, h, d, base_t, sup) in zip(axes, casos):
        # bidón (aprox.) y pico
        # bidón aproximado: centro a 16 cm de la cara exterior, radio 135, hombro elíptico
        cx, rb, z_body, z_neck = -160.0, 135.0, 20.0, 150.0
        zs = np.linspace(z_body, z_neck, 30)
        rs = 27 + 108 * np.sqrt(np.clip(1 - ((zs - z_body) / (z_neck - z_body)) ** 2, 0, 1))
        front = [(cx + rb, -300)] + [(cx + r, z) for r, z in zip(rs, zs)] + [(cx + 27, 200), (cx - 300, 200), (cx - 300, -300)]
        ax.add_patch(Polygon(front, closed=True, fc="#B5D4F4", ec="#185FA5", alpha=0.35, lw=0.8))
        ax.add_patch(Rectangle((cx - 30, 200), 60, 110, fc="#F1EFE8", ec="#888780"))
        ax.plot([cx + 30, -70, -55, -50], [255, 262, 255, 237], color="#888780", lw=3, solid_capstyle="round")
        ax.text(-195, 280, "bidón y bomba: aproximados", fontsize=8, color="#666")
        # tabla frontal
        ax.add_patch(Rectangle((-s.TABLA_ESPESOR, -s.TABLA_ALTO), s.TABLA_ESPESOR, s.TABLA_ALTO,
                               fc=MADERA, ec=MADERA_B))
        # corte del soporte en y=0
        sec = principal.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
        if sec is not None:
            for ent in sec.discrete:
                ax.fill(ent[:, 0], ent[:, 2], color=VERDE, alpha=0.9, lw=0)
        # silueta del soporte (proyección) en tono claro
        v = principal.vertices
        # suplementos
        if sup:
            t0 = 0.0
            for key in sup:
                hh, od = (s.SUP_A_H, s.SUP_A_OD) if key == "A" else (s.SUP_B_H, s.SUP_B_OD)
                corners = [(-od / 2, t0), (od / 2, t0), (od / 2, t0 + hh), (-od / 2, t0 + hh)]
                pts = [((s.B + z * s.U + x * s.N)[0], (s.B + z * s.U + x * s.N)[2]) for x, z in corners]
                ax.add_patch(Polygon(pts, closed=True, fc="#9FE1CB", ec=VERDE, lw=0.8))
                t0 += hh - 5.0
        # botella
        ax.add_patch(Polygon(bottle_outline(h, d, base_t), closed=True, fc=AZUL, ec="#185FA5", alpha=0.25, lw=1))
        mx, mz = s.mouth_position(h, base_t)
        # chorro
        ax.plot([-50, -44, mx], [237, 222, mz], color=AZUL, lw=2)
        ax.plot(mx, mz, "o", color="#185FA5", ms=4)
        ax.set_title(nombre, fontsize=12)
        ax.set_aspect("equal")
        ax.set_xlim(-200, 230)
        ax.set_ylim(-150, 300)
        ax.axhline(0, color="#bbb", lw=0.5, ls=":")
        ax.grid(alpha=0.15)
        ax.set_xlabel("mm (0 = cara exterior de la tabla)")
        ax.text(-195, -140, f"boca: {(mx - s.PICO_X):.0f} mm adelante y {s.PICO_Z - mz:.0f} mm abajo del pico",
                fontsize=9, color="#444")
    axes[0].set_ylabel("mm (0 = canto superior de la tabla)")
    fig.suptitle("Vista de costado (corte por el centro del soporte)", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "vista_costado.png"), dpi=130)


def shade(mesh, light=np.array([0.4, -0.7, 0.6])):
    n = mesh.face_normals
    l = light / np.linalg.norm(light)
    return np.clip(0.35 + 0.65 * (n @ l), 0, 1)


def iso_view():
    principal = mesh_of(s.soporte_principal())
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="3d")
    # tabla frontal (caja)
    tabla = trimesh.creation.box(extents=[s.TABLA_ESPESOR, 260, s.TABLA_ALTO])
    tabla.apply_translation([-s.TABLA_ESPESOR / 2, 0, -s.TABLA_ALTO / 2])
    # botella 1,5 L como cilindro
    bot = trimesh.creation.cylinder(radius=45, height=215, sections=64)
    bot.apply_translation([0, 0, 215 / 2])
    rot = trimesh.transformations.rotation_matrix(math.radians(-s.INCLINACION), [0, 1, 0])
    bot.apply_transform(rot)
    bot.apply_translation(s.B)
    neck = trimesh.creation.cone(radius=45, height=95, sections=64)
    neck.apply_translation([0, 0, 215])
    neck.apply_transform(rot); neck.apply_translation(s.B)
    tris, cols_all = [], []
    for mesh, base, alpha in [(tabla, MADERA, 1.0), (principal, VERDE, 1.0), (bot, AZUL, 0.22), (neck, AZUL, 0.22)]:
        sh = shade(mesh)
        rgb = np.array(matplotlib.colors.to_rgb(base))
        cols = np.clip(rgb[None, :] * (0.55 + 0.6 * sh[:, None]), 0, 1)
        tris.append(mesh.vertices[mesh.faces])
        cols_all.append(np.c_[cols, np.full(len(cols), alpha)])
    pc = Poly3DCollection(np.concatenate(tris), facecolors=np.concatenate(cols_all), edgecolors="none")
    ax.add_collection3d(pc)
    ax.set_xlim(-120, 200); ax.set_ylim(-160, 160); ax.set_zlim(-140, 180)
    ax.set_box_aspect((320, 320, 320))
    ax.view_init(elev=22, azim=-35)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "vista_3d.png"), dpi=120)


def piece_views():
    names = [("soporte_principal.stl", "Soporte principal"), ("suplemento_A_60mm.stl", "Suplemento A (60 mm)"),
             ("suplemento_B_40mm.stl", "Suplemento B (40 mm)"), ("reductor_aro_1L.stl", "Reductor aro 1 L"),
             ("reductor_aro_500ml.stl", "Reductor aro 500 ml")]
    fig = plt.figure(figsize=(16, 4.2))
    for i, (f, t) in enumerate(names):
        m = trimesh.load(os.path.join(OUT, f))
        ax = fig.add_subplot(1, 5, i + 1, projection="3d")
        sh = shade(m)
        rgb = np.array(matplotlib.colors.to_rgb(VERDE))
        cols = np.clip(rgb[None, :] * (0.55 + 0.6 * sh[:, None]), 0, 1)
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=cols, edgecolors="none"))
        e = m.extents.max() / 2 + 5
        c = m.bounds.mean(axis=0)
        ax.set_xlim(c[0] - e, c[0] + e); ax.set_ylim(c[1] - e, c[1] + e); ax.set_zlim(c[2] - e, c[2] + e)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=25, azim=-55); ax.set_axis_off()
        ax.set_title(f"{t}\n{m.extents[0]:.0f}×{m.extents[1]:.0f}×{m.extents[2]:.0f} mm", fontsize=10)
    fig.suptitle("Piezas en orientación de impresión", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "piezas_impresion.png"), dpi=120)


if __name__ == "__main__":
    side_view()
    iso_view()
    piece_views()
    print("ok")

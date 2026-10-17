import base64, json, io
import trimesh
import soporte as s

def b64(m):
    mm = m.to_mesh()
    t = trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts)
    buf = io.BytesIO(); t.export(buf, file_type="stl")
    return base64.b64encode(buf.getvalue()).decode()

data = {
  "principal": b64(s.soporte_principal()),
  "supA": b64(s.to_global(s.suplemento_a())),
  "supB": b64(s.to_global(s.suplemento_b().translate([0, 0, s.SUP_A_H - 5.0]))),
  "red1": b64(s.to_global(s.reductor_1l().translate([0, 0, s.ARO_T]))),
  "red05": b64(s.to_global(s.reductor_500().translate([0, 0, s.ARO_T]))),
  "B": s.B.tolist(), "incl": s.INCLINACION,
  "tabla": [s.TABLA_ESPESOR, s.TABLA_ALTO], "pico": [s.PICO_X, s.PICO_Z],
}
json.dump(data, open("out/viewer_data.json", "w"))
print(sum(len(v) for v in data.values() if isinstance(v, str)) // 1024, "KB")

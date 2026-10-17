"""
Soporte para llenar botellas desde el bidón - modelo paramétrico.

Ejes (en mm):
  X = hacia afuera del mueble (0 = cara exterior de la tabla frontal)
  Y = a lo largo de la tabla
  Z = hacia arriba (0 = canto superior de la tabla frontal)

Piezas que exporta:
  soporte_principal.stl   gancho en U + espalda + aro en C + copa (para 1,5 L)
  suplemento_A_60mm.stl   para 1 L (solo) y 500 ml (debajo del B)
  suplemento_B_40mm.stl   para 500 ml (encima del A)
  reductor_aro_1L.stl     se encastra dentro del aro en C
  reductor_aro_500ml.stl  se encastra dentro del aro en C
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, set_circular_segments

set_circular_segments(128)

# ---------------- Medidas del mueble y del pico (de Santi) ----------------
TABLA_ESPESOR = 20.0      # mm (en la foto parece 18-19; el gancho flexa para 18-20)
TABLA_ALTO = 70.0         # mm
PICO_X = -50.0            # punta del pico: 5 cm hacia adentro de la cara exterior
PICO_Z = 237.0            # punta del pico: 23,7 cm sobre el canto de la tabla

# ---------------- Botellas (rangos estándar) ----------------
BOT15_D_MAX = 92.0        # 1,5 L: 88-92 mm
BOT15_H_REF = 320.0       # 1,5 L: 310-330 mm
BOT1_H_REF = 258.0        # 1 L: 255-260 mm
BOT05_H_REF = 220.0       # 500 ml: 210-227 mm

# ---------------- Decisiones de diseño ----------------
INCLINACION = 30.0        # grados respecto de la vertical (60° respecto del piso)
BOCA_X = PICO_X + 10.0    # el chorro avanza ~1 cm: la boca queda 1 cm por delante de la punta del pico
BOCA_Z = PICO_Z - 22.0    # y 22 mm por debajo con la botella de 320 mm (13 a 31 mm según la altura)
HOLGURA_BOTELLA = 2.0     # radial entre botella y aro/copa
PARED = 3.5
ANCHO_GANCHO = 50.0       # a lo largo de la tabla
COPA_PROF = 30.0          # profundidad de la copa en la parte de atrás
COPA_PROF_FRENTE = 12.0   # la copa es baja adelante para entrar la base fácil
ARO_T = 150.0             # altura del aro medida desde el piso de la copa (sobre el eje)
ARO_ALTO = 18.0
ARO_CORTE = 8.0           # el aro queda abierto adelante a partir de 8 mm del eje

R_IN = BOT15_D_MAX / 2 + HOLGURA_BOTELLA          # 48
R_OUT = R_IN + PARED                              # 51.5

th = math.radians(INCLINACION)
U = np.array([-math.sin(th), 0.0, math.cos(th)])  # eje de la botella, hacia la boca
N = np.array([math.cos(th), 0.0, math.sin(th)])   # perpendicular, hacia el frente
B = np.array([BOCA_X, 0.0, BOCA_Z]) - BOT15_H_REF * U   # centro del piso de la copa


def to_global(m: Manifold) -> Manifold:
    """Pasa de coordenadas de la botella (z = eje) a coordenadas del mueble."""
    return m.rotate([0.0, -INCLINACION, 0.0]).translate(B.tolist())


def profile_xz(points, width, y_center=0.0) -> Manifold:
    """Extruye un polígono dibujado en el plano XZ a lo ancho de Y."""
    cs = CrossSection([[(float(x), float(z)) for x, z in points]])
    m = cs.extrude(width)                 # polígono en XY, extruido en +Z
    m = m.rotate([90.0, 0.0, 0.0])        # y->z, z->-y
    return m.translate([0.0, y_center + width / 2, 0.0])


def tube(r_out, r_in, z0, z1) -> Manifold:
    h = z1 - z0
    outer = Manifold.cylinder(h, r_out).translate([0, 0, z0])
    if r_in <= 0:
        return outer
    inner = Manifold.cylinder(h + 2, r_in).translate([0, 0, z0 - 1])
    return outer - inner


def front_cut(x_from, z0, z1, big=200.0) -> Manifold:
    return Manifold.cube([big, big, z1 - z0]).translate([x_from, -big / 2, z0])


# ---------------- Pieza principal ----------------
def soporte_principal() -> Manifold:
    # Copa (en coordenadas de la botella)
    copa = tube(R_OUT, 0, -4.0, COPA_PROF)
    copa = copa - front_cut(R_IN * 0.55, COPA_PROF_FRENTE, COPA_PROF + 5)

    # Aro en C
    aro = tube(R_OUT, 0, ARO_T, ARO_T + ARO_ALTO) - front_cut(ARO_CORTE, ARO_T - 1, ARO_T + ARO_ALTO + 1)

    # Rieles que unen copa y aro: atrás y a los costados
    rieles = []
    for ang in (90.0, 180.0, 270.0):
        r = Manifold.cube([PARED + 1.5, 10.0, ARO_T + 2 - 10.0]).translate([R_IN - 0.5, -5.0, 10.0])
        rieles.append(r.rotate([0.0, 0.0, ang]))
    cuerpo = copa + aro
    for r in rieles:
        cuerpo = cuerpo + r
    cuerpo = to_global(cuerpo)

    # Gancho en U + espalda (perfil en XZ). La espalda sube hasta tocar la parte de atrás del aro.
    aro_atras = B - R_OUT * N + ARO_T * U
    ESPALDA_TOPE = float(aro_atras[2]) + 14.0
    gap = TABLA_ESPESOR + 0.5
    gancho = profile_xz([
        (-gap - 4.0, -32.0), (-gap, -32.0), (-gap, -26.0), (-gap + 1.8, -24.0),   # labio que aprieta
        (-gap + 1.8, -21.0), (-gap, -19.0), (-gap, 0.0),
        (0.0, 0.0), (0.0, -TABLA_ALTO - 4.0), (7.0, -TABLA_ALTO - 4.0),
        (7.0, ESPALDA_TOPE), (-4.0, ESPALDA_TOPE), (-4.0, 5.0), (-gap - 4.0, 5.0),
    ], ANCHO_GANCHO)

    # Brazo inferior: de la base de la espalda a la parte de atrás de la copa
    p_bajo = B - (R_OUT - 3.0) * N + (-4.0) * U
    p_alto = B - (R_OUT - 3.0) * N + (COPA_PROF - 2.0) * U
    brazo = profile_xz([
        (0.0, -TABLA_ALTO - 4.0), (p_bajo[0], p_bajo[2]), (p_alto[0], p_alto[2]),
        (7.0, -40.0), (0.0, -40.0),
    ], 26.0)

    pieza = cuerpo + gancho + brazo

    # Vaciar el lugar de la botella (garantiza holgura en todo el recorrido)
    envolvente = to_global(Manifold.cylinder(400.0, R_IN).translate([0, 0, 0]))
    pieza = pieza - envolvente
    # La tabla tampoco puede quedar ocupada
    tabla = Manifold.cube([gap, 300.0, TABLA_ALTO + 50]).translate([-gap, -150.0, -TABLA_ALTO - 50])
    pieza = pieza - tabla
    return pieza


# ---------------- Suplementos (se apoyan en la copa) ----------------
def suplemento(od, h, recess_id, recess_depth=5.0) -> Manifold:
    s = Manifold.cylinder(h, od / 2)
    s = s - Manifold.cylinder(recess_depth + 1, recess_id / 2).translate([0, 0, h - recess_depth])
    s = s - Manifold.cylinder(h - recess_depth - 6.0, od / 2 - 6.0).translate([0, 0, 3.0])  # alivianado
    return s


SUP_A_H, SUP_B_H = 60.0, 40.0
SUP_A_OD, SUP_B_OD = 2 * R_IN - 2.0, 86.0         # 94 y 86 mm
SUP_A_RECESS, SUP_B_RECESS = 89.0, 74.0


def suplemento_a():
    return suplemento(SUP_A_OD, SUP_A_H, SUP_A_RECESS)


def suplemento_b():
    return suplemento(SUP_B_OD, SUP_B_H, SUP_B_RECESS)


# ---------------- Reductores del aro ----------------
def reductor(r_in) -> Manifold:
    banda = tube(R_IN - 0.4, r_in, 0.0, ARO_ALTO)
    pestana = tube(R_OUT + 1.5, r_in, ARO_ALTO, ARO_ALTO + 2.5)      # cuelga del borde del aro
    labio = tube(R_OUT + 1.5, R_OUT + 0.3, ARO_ALTO - 4.0, ARO_ALTO)  # abraza el aro por fuera
    r = banda + pestana + labio
    return r - front_cut(ARO_CORTE, -1, ARO_ALTO + 4)


def reductor_1l():
    return reductor(44.0)      # botellas de 80-85 mm


def reductor_500():
    return reductor(36.5)      # botellas de 65-70 mm


# ---------------- Utilidades ----------------
def mouth_position(h_bottle, base_t=0.0):
    p = B + (base_t + h_bottle) * U
    return p[0], p[2]


if __name__ == "__main__":
    import trimesh, os
    out = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(out, exist_ok=True)

    def save(m: Manifold, name, print_rot=None):
        if print_rot is not None:
            m = m.rotate(print_rot)
        mesh = m.to_mesh()
        tm = trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=True)
        tm.apply_translation([-tm.bounds[0][0] - tm.extents[0] / 2,
                              -tm.bounds[0][1] - tm.extents[1] / 2,
                              -tm.bounds[0][2]])
        tm.export(os.path.join(out, name))
        return tm

    principal = soporte_principal()
    # Orientación de impresión: eje de la copa vertical, piso de la copa sobre la cama
    save(principal, "soporte_principal.stl", print_rot=[0.0, INCLINACION, 0.0])
    save(suplemento_a(), "suplemento_A_60mm.stl")
    save(suplemento_b(), "suplemento_B_40mm.stl")
    save(reductor_1l().rotate([180, 0, 0]), "reductor_aro_1L.stl")
    save(reductor_500().rotate([180, 0, 0]), "reductor_aro_500ml.stl")
    # También la pieza principal en posición de uso, para los renders
    mm = principal.to_mesh()
    trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts).export(os.path.join(out, "_principal_en_uso.stl"))
    print("B =", B.round(1))

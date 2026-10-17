"""
Soporte del bidón V.2.1 - abraza el cuello y se recuesta contra la panza del bidón.

Ejes (en mm):
  X = hacia donde apunta el pico (0 = eje del cuello)
  Y = de costado
  Z = hacia arriba (0 = unión cuello-hombro)

Cómo trabaja:
  - El anillo se apoya sobre la base del cuello y toma el peso (vertical).
  - La palanca de la botella hace girar el soporte hacia el bidón; un apoyo curvo en la
    espalda de la cuna se recuesta contra la parte más ancha del bidón (270 mm, estándar)
    y toma ese giro. No depende de la forma del hombro.
  - Un tornillito atrás del anillo, de apriete a mano, saca el juego contra el cuello.

Piezas (PETG):
  collar.stl           anillo + brazo + espalda con lengüeta
  cuna.stl             copa + aro en C + riel + bolsillo + apoyo contra el bidón
  tornillo_trasero.stl M12 impreso con perilla
  Suplementos y reductores para 1 L y 500 ml: los mismos de la V1.1.

Para ponerlo: sacar la bomba, bajar el collar por el cuello, volver a poner la bomba,
girar el collar hasta que el brazo quede debajo del pico y bajar la cuna en la lengüeta
hasta que haga clic.
"""
import math
import numpy as np
from manifold3d import Manifold, CrossSection, set_circular_segments

set_circular_segments(96)

# ---------------- Medidas de Santi ----------------
CUELLO_D = 55.0           # estándar de bidones retornables de 20 L
CUELLO_LIBRE = 30.0       # entre la unión con el hombro y el adaptador gris
PICO_X = 120.0            # 35 (radio de la bomba, 70 mm) + 85 (costado del cuerpo a la punta)
PICO_Z = 110.0            # punta sobre la unión cuello-hombro
BIDON_R = 135.0           # 270 mm, estándar
PANZA_Z = -95.0           # altura estimada de la parte más ancha (foto del bidón rojo)

# ---------------- Botella (igual que V1.1) ----------------
BOT15_D_MAX = 92.0
BOT15_H_REF = 320.0
INCLINACION = 30.0
BOCA_X = PICO_X + 10.0    # el chorro avanza ~1 cm
BOCA_Z = PICO_Z - 22.0
HOLGURA_BOTELLA = 2.0
PARED = 3.5
COPA_PROF = 30.0
COPA_PROF_FRENTE = 12.0
ARO_T = 130.0
ARO_ALTO = 18.0
ARO_CORTE = 8.0
R_IN = BOT15_D_MAX / 2 + HOLGURA_BOTELLA   # 48
R_OUT = R_IN + PARED                       # 51.5

# ---------------- Collar ----------------
ANILLO_RI = CUELLO_D / 2 + 0.3
ANILLO_RE = ANILLO_RI + 6.0
ANILLO_Z0, ANILLO_Z1 = 0.5, 28.0
BRAZO_ANCHO = 30.0

# ---------------- Riel, bolsillo y lengüeta (radial = distancia detrás del eje de la botella) ----------------
RIEL_R0, RIEL_R1 = R_IN - 0.5, R_IN + 14.0
RIEL_ANCHO = 24.0
RIEL_T0 = 10.0
BOLS_T0, BOLS_T1 = 150.0, 195.0            # bolsillo arriba del aro, abierto hacia arriba
BOLS_R0, BOLS_R1 = R_OUT + 0.5, R_IN + 22.0
BOLS_ANCHO = 44.0
LENG_R0, LENG_R1 = BOLS_R0 + 3.0, BOLS_R1 - 3.0   # lengüeta (hueco del bolsillo = lengüeta + 0,3)
LENG_ANCHO = 32.0
LENG_T0 = BOLS_T0 + 4.0                     # la lengüeta asienta en el fondo del bolsillo
HOLG = 0.3
ESPALDA_T1 = 275.0
TRABA_T = (163.0, 170.0)                    # dientes de la traba y ventanas del bolsillo

# ---------------- Tornillo trasero ----------------
TT_D = 12.0
TT_P = 1.75
TT_PROF = 1.1
TT_Z = (ANILLO_Z0 + ANILLO_Z1) / 2

th = math.radians(INCLINACION)
U = np.array([-math.sin(th), 0.0, math.cos(th)])  # eje de la botella, hacia la boca
N = np.array([math.cos(th), 0.0, math.sin(th)])   # perpendicular, hacia afuera
B = np.array([BOCA_X, 0.0, BOCA_Z]) - BOT15_H_REF * U   # centro del piso de la copa


def to_global(m):
    return m.rotate([0.0, -INCLINACION, 0.0]).translate(B.tolist())


def tube(r_out, r_in, z0, z1):
    h = z1 - z0
    outer = Manifold.cylinder(h, r_out).translate([0, 0, z0])
    if r_in <= 0:
        return outer
    return outer - Manifold.cylinder(h + 2, r_in).translate([0, 0, z0 - 1])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def bbox(r0, r1, ancho, t0, t1):
    """Caja detrás de la botella, en coordenadas de la botella (r = distancia hacia atrás)."""
    return box(-r1, -r0, -ancho / 2, ancho / 2, t0, t1)


def front_cut(x_from, z0, z1, big=200.0):
    return box(x_from, x_from + big, -big / 2, big / 2, z0, z1)


def envolvente_botella():
    return to_global(Manifold.cylinder(420.0, R_IN))


def bidon_cilindro():
    return Manifold.cylinder(500, BIDON_R + 0.5).translate([0, 0, -450])


# ---------------- Rosca ----------------
def rosca(r_major, paso, prof, largo, extra=0.0):
    n = 144
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        f = a / (2 * math.pi)
        if f < 0.125:
            k = 1.0
        elif f < 0.5:
            k = 1.0 - (f - 0.125) / 0.375
        elif f < 0.625:
            k = 0.0
        else:
            k = (f - 0.625) / 0.375
        r = r_major - prof + prof * k + extra
        pts.append((r * math.cos(a), r * math.sin(a)))
    vueltas = largo / paso
    return CrossSection([pts]).extrude(largo, n_divisions=int(vueltas * 24), twist_degrees=360.0 * vueltas)


# ---------------- Collar ----------------
def collar():
    anillo = tube(ANILLO_RE, 0, ANILLO_Z0, ANILLO_Z1)
    brazo = box(20.0, 112.0, -BRAZO_ANCHO / 2, BRAZO_ANCHO / 2, ANILLO_Z0, ANILLO_Z1)
    # Taco trasero para el tornillo
    taco = box(-ANILLO_RE - 9.0, -ANILLO_RI - 1.0, -11.0, 11.0, ANILLO_Z0, ANILLO_Z1)

    # Lengüeta que entra en el bolsillo de la cuna + espalda que sube hasta el brazo
    leng = bbox(LENG_R0, LENG_R1, LENG_ANCHO, LENG_T0, BOLS_T1 + 2.0)
    leng = leng - bbox(LENG_R0 - 1, LENG_R1 + 1, 2.4, LENG_T0 - 1, LENG_T0 + 34.0)  # ranura: las dos mitades flexan
    for s in (1, -1):  # dientes de la traba (rampa abajo, tope arriba)
        d = CrossSection([[(0, TRABA_T[0]), (1.2, TRABA_T[1] - 1.5), (1.2, TRABA_T[1]), (0, TRABA_T[1])]])
        d = d.extrude(LENG_R1 - LENG_R0 - 4).rotate([90, 0, 0])  # perfil en (y, t), extruido en x
        d = d.rotate([0, 0, 90]).translate([-(LENG_R1 - 2), 0, 0])
        diente = d.translate([0, LENG_ANCHO / 2, 0]) if s == 1 else d.mirror([0, 1, 0]).translate([0, -LENG_ANCHO / 2, 0])
        leng = leng + diente
    esp = bbox(BOLS_R0 + 0.5, BOLS_R1, 40.0, BOLS_T1 + 1.0, ESPALDA_T1)
    pieza = anillo + brazo + taco + to_global(leng + esp)

    pieza = pieza - Manifold.cylinder(60, ANILLO_RI).translate([0, 0, -10])
    pieza = pieza - Manifold.cylinder(3.5, ANILLO_RI + 3, ANILLO_RI).translate([0, 0, ANILLO_Z0 - 0.01])
    agujero = rosca(TT_D / 2, TT_P, TT_PROF, 20.0, extra=HOLG).rotate([0, -90, 0]).translate([-ANILLO_RI + 2, 0, TT_Z])
    pieza = pieza - agujero
    pieza = pieza - envolvente_botella()
    return pieza


# ---------------- Cuna ----------------
def cuna():
    copa = tube(R_OUT, 0, -4.0, COPA_PROF) - front_cut(R_IN * 0.55, COPA_PROF_FRENTE, COPA_PROF + 5)
    aro = tube(R_OUT, 0, ARO_T, ARO_T + ARO_ALTO) - front_cut(ARO_CORTE, ARO_T - 1, ARO_T + ARO_ALTO + 1)
    cuerpo = copa + aro
    for ang in (90.0, 270.0):
        cuerpo = cuerpo + box(R_IN - 0.5, R_IN + 5.0, -5.0, 5.0, 10.0, ARO_T + 2).rotate([0, 0, ang])
    riel = bbox(RIEL_R0, RIEL_R1, RIEL_ANCHO, RIEL_T0, BOLS_T0 + 2)
    bolsillo = bbox(RIEL_R0, BOLS_R1, BOLS_ANCHO, BOLS_T0, BOLS_T1)
    hueco = bbox(LENG_R0 - HOLG, LENG_R1 + HOLG, LENG_ANCHO + 2 * HOLG, LENG_T0, BOLS_T1 + 5)
    ventanas = bbox(LENG_R0 + 1, LENG_R1 - 1, BOLS_ANCHO + 2, TRABA_T[0] - 0.5, TRABA_T[1] + 1.0)
    bolsillo = bolsillo - hueco - ventanas
    cuerpo = to_global(cuerpo + riel + bolsillo)

    # Apoyo contra la panza del bidón: sale de la espalda del riel hacia el bidón
    apoyo = box(BIDON_R - 5.0, 190.0, -30.0, 30.0, PANZA_Z - 18.0, PANZA_Z + 14.0)
    puente = to_global(bbox(RIEL_R0, BOLS_R1, RIEL_ANCHO, 110.0, BOLS_T0 + 1))
    apoyo = (apoyo - bidon_cilindro()) + (puente ^ box(0, 300, -50, 50, -200, PANZA_Z + 14.0))
    cuerpo = cuerpo + apoyo
    cuerpo = cuerpo - to_global(hueco + ventanas) - envolvente_botella()
    return cuerpo


# ---------------- Tornillo trasero ----------------
def tornillo_trasero():
    r = rosca(TT_D / 2 - 0.15, TT_P, TT_PROF, 16.0)
    punta = Manifold.cylinder(2.0, TT_D / 2 - TT_PROF - 0.2, TT_D / 2 - TT_PROF - 1.5).translate([0, 0, -2.0])
    perilla = Manifold.cylinder(9.0, 13.0).translate([0, 0, 16.0])
    for i in range(10):
        perilla = perilla - Manifold.cylinder(11, 2.0).translate([13.6, 0, 15.0]).rotate([0, 0, 36 * i])
    return (r + punta + perilla).translate([0, 0, 2.0])


def mouth_position(h_bottle, base_t=0.0):
    p = B + (base_t + h_bottle) * U
    return p[0], p[2]


if __name__ == "__main__":
    import trimesh, os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".stl"):
            os.remove(os.path.join(out, f))

    def tm_of(m):
        mesh = m.to_mesh()
        return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=True)

    def save(m, name, rot=None):
        if rot is not None:
            m = m.rotate(rot)
        t = tm_of(m)
        t.apply_translation([-t.bounds[0][0] - t.extents[0] / 2, -t.bounds[0][1] - t.extents[1] / 2, -t.bounds[0][2]])
        t.export(os.path.join(out, name))
        print(f"{name:22s} {t.extents.round(1)} mm  vol {t.volume/1000:.1f} cm3  watertight={t.is_watertight}")
        return t

    c = collar()
    k = cuna()
    tm_of(c).export(os.path.join(out, "_collar_en_uso.stl"))
    tm_of(k).export(os.path.join(out, "_cuna_en_uso.stl"))
    save(c, "collar.stl", rot=[180.0, 0.0, 0.0])             # cara de arriba del anillo y del brazo sobre la cama
    save(k, "cuna.stl", rot=[0.0, INCLINACION, 0.0])         # copa sobre la cama
    save(tornillo_trasero(), "tornillo_trasero.stl", rot=[180.0, 0.0, 0.0])  # perilla sobre la cama
    print("B =", B.round(1), "boca 1,5 L =", np.round(mouth_position(320), 1))
    print("interferencia collar-cuna mm3:", round((c ^ k).volume(), 1))

import base64, json, math, trimesh
from manifold3d import Manifold, set_circular_segments
import soporte_v2 as S
set_circular_segments(64)
S.rosca = lambda r_major, paso, prof, largo, extra=0.0: Manifold.cylinder(largo, r_major - prof/2 + extra)
def b64(m):
    mm=m.to_mesh(); t=trimesh.Trimesh(mm.vert_properties[:,:3], mm.tri_verts)
    return base64.b64encode(t.export(file_type="stl")).decode()
# Suplementos y reductores de la V1.1 (mismas medidas), ubicados en uso
def suplemento(od,h,rec,rd=5.0):
    s=Manifold.cylinder(h,od/2)-Manifold.cylinder(rd+1,rec/2).translate([0,0,h-rd])
    return s-Manifold.cylinder(h-rd-6,od/2-6).translate([0,0,3])
def reductor(r_in):
    banda=S.tube(S.R_IN-0.4,r_in,0,S.ARO_ALTO); pest=S.tube(S.R_OUT+1.5,r_in,S.ARO_ALTO,S.ARO_ALTO+2.5)
    labio=S.tube(S.R_OUT+1.5,S.R_OUT+0.3,S.ARO_ALTO-4,S.ARO_ALTO)
    return (banda+pest+labio)-S.front_cut(S.ARO_CORTE,-1,S.ARO_ALTO+4)
supA=S.to_global(suplemento(2*S.R_IN-2,60,89)); supB=S.to_global(suplemento(86,40,74).translate([0,0,60]))
red1=S.to_global(reductor(44).translate([0,0,S.ARO_T])); red05=S.to_global(reductor(36.5).translate([0,0,S.ARO_T]))
tt=S.tornillo_trasero().rotate([0,-90,0]).translate([-27.8,0,S.TT_Z])
D={"collar":b64(S.collar()),"cuna":b64(S.cuna()),"tornillo":b64(tt),"supA":b64(supA),"supB":b64(supB),"red1":b64(red1),"red05":b64(red05),
   "B":[float(x) for x in S.B],"incl":S.INCLINACION,"pico":[S.PICO_X,S.PICO_Z],"aroT":S.ARO_T}
open("out/viewer_data.js","w").write("const D = "+json.dumps(D)+";")
print({k:len(v) for k,v in D.items() if isinstance(v,str)})

import math, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from manifold3d import Manifold, CrossSection
import os
import soporte_v2 as S
os.makedirs("out", exist_ok=True)

# Bidón aproximado: cuello 55 x 30, hombro elíptico que baja 100 mm hasta r = 135
def perfil_bidon(caida=100.0):
    pts=[(0,-400),(135,-400),(135,-caida)]
    for i in range(1,30):
        f=math.pi/2*i/30
        pts.append((27.5+107.5*math.cos(f), -caida*(1-math.sin(f))))
    pts += [(27.5,0),(27.5,30),(31,30),(31,47),(34,47),(34,72),(35,72),(35,190),(0,190)]
    return pts
def bidon(caida):
    return CrossSection([perfil_bidon(caida)]).revolve(96)
c=S.collar(); k=S.cuna()
for caida in (70,100,130):
    b=bidon(caida)
    print(f"hombro baja {caida}: choque collar {(c^b).volume():.0f} mm3, cuna {(k^b).volume():.0f} mm3")
# Tabla del mueble (V1): canto a 237 bajo el pico, cara exterior 50 mm fuera del pico
tabla=S.box(150,170,-200,200,-197,-127)
print("choque tabla: collar", (c^tabla).volume(), "cuna", (k^tabla).volume())
print("cuna punto mas bajo z=", round(k.bounding_box()[2],1), " x min cuna", round(k.bounding_box()[0],1))

def tm(m):
    mm=m.to_mesh(); return trimesh.Trimesh(mm.vert_properties[:,:3], mm.tri_verts)
# botella 1,5 L esquemática
bot = S.to_global(Manifold.cylinder(230,45)+Manifold.cylinder(60,45,14).translate([0,0,230])+Manifold.cylinder(30,14).translate([0,0,290]))

fig=plt.figure(figsize=(13,7))
ax=fig.add_subplot(1,2,1)
p=np.array(perfil_bidon(100)); ax.fill(np.r_[p[:,0],-p[::-1,0]], np.r_[p[:,1],p[::-1,1]], color="#cfe3f3", ec="#5b8db8", lw=1, label="bidón (hombro estimado)")
ax.plot([35,40,85,100,120],[85,90,118,118,110],color="#777",lw=3,solid_capstyle="round",label="pico")
for m,col,lab in ((tm(bot),"#bbbbbb","botella 1,5 L"),(tm(k),"#d9822b","cuna"),(tm(c),"#2b7bd9","collar")):
    sec=m.section(plane_origin=[0,0,0],plane_normal=[0,1,0])
    if sec is None: continue
    for e in sec.discrete: ax.fill(e[:,0],e[:,2],color=col,alpha=.85 if lab!="botella 1,5 L" else .35,ec="k",lw=.4)
    ax.plot([],[],color=col,lw=6,label=lab)
ax.add_patch(plt.Rectangle((150,-197),20,70,color="#a0703c",alpha=.8)); ax.plot([],[],color="#a0703c",lw=6,label="tabla del mueble (V1)")
ax.plot(120,110,"ro",ms=4); ax.annotate("punta del pico",(120,110),(150,135),fontsize=8,arrowprops=dict(arrowstyle="-",lw=.5))
ax.set_aspect("equal"); ax.set_xlim(-160,360); ax.set_ylim(-260,200); ax.grid(alpha=.3); ax.legend(fontsize=7,loc="lower left"); ax.set_title("Corte de costado (mm)")
ax2=fig.add_subplot(1,2,2,projection="3d")
for m,col in ((tm(c),"#2b7bd9"),(tm(k),"#d9822b")):
    ax2.add_collection3d(Poly3DCollection(m.vertices[m.faces],facecolors=col,edgecolors=col,linewidths=0,shade=True))
ax2.set_xlim(-60,320); ax2.set_ylim(-190,190); ax2.set_zlim(-230,60); ax2.set_box_aspect((380,380,290)); ax2.view_init(22,-130); ax2.set_axis_off(); ax2.set_title("Collar (azul) + cuna (naranja)")
plt.tight_layout(); plt.savefig("out/v2_render.png",dpi=130)


tt = S.tornillo_trasero().rotate([0,-90,0]).translate([-27.8, 0, S.TT_Z])
print("tornillo trasero vs bidón:", round((tt^bidon(100)).volume()), " vs collar:", round((tt^c).volume()))
print("collar vs botella", round((c^bot).volume()), "cuna vs botella", round((k^bot).volume()))
fig=plt.figure(figsize=(9,8)); ax2=fig.add_subplot(111,projection="3d")
b=bidon(100)
for m,col in ((tm(b - S.box(-300,300,-300,300,-400,-200)),"#cfe3f3"),(tm(c),"#2b7bd9"),(tm(k),"#d9822b"),(tm(tt),"#555555"),(tm(bot),"#e8e8e8")):
    ax2.add_collection3d(Poly3DCollection(m.vertices[m.faces],facecolors=col,edgecolors=col,linewidths=0,shade=True,alpha=.5 if col in("#cfe3f3","#e8e8e8") else 1))
ax2.set_xlim(-140,340); ax2.set_ylim(-240,240); ax2.set_zlim(-260,200); ax2.set_box_aspect((480,480,460)); ax2.view_init(14,-120); ax2.set_axis_off()
plt.tight_layout(); plt.savefig("out/v2_conjunto.png",dpi=120)

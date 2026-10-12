"""Generate an original ASCII hourglass as GitHub-compatible SVG and text."""
from pathlib import Path
import html
import numpy as np

ROOT = Path(__file__).parent
COLS, ROWS = 91, 57

def scene(p):
    x, y, z = p.T
    radial = np.sqrt(x*x + z*z)
    # Lathed metal caps with a stepped rim.
    caps = np.maximum(radial - 1.10, np.abs(np.abs(y) - 1.55) - .085)
    rims = np.maximum(radial - 1.19, np.abs(np.abs(y) - 1.66) - .045)
    metal = np.minimum(caps, rims)
    for px, pz in [(-.94,-.40), (.94,-.40), (-.94,.40), (.94,.40)]:
        post = np.maximum(np.sqrt((x-px)**2 + (z-pz)**2)-.050, np.abs(y)-1.54)
        metal = np.minimum(metal, post)
    # A hollow silhouette, cut through its front to reveal the falling sand.
    radius = .085 + .76 * np.minimum(np.abs(y)/1.43, 1.2)**1.45
    shell = np.maximum(np.abs(radial-radius)-.018, np.abs(y)-1.43)
    shell = np.maximum(shell, z-.20)
    # Sand remaining in the upper bowl and collecting in the lower bowl.
    upper = np.maximum(radial-radius+.038, np.maximum(.06-y, y-.78))
    pile_radius = np.maximum(0, (-y-.40)*.73)
    lower = np.maximum(radial-pile_radius, np.maximum(-1.43-y, y+.40))
    stream = np.maximum(radial-.014, np.maximum(-.50-y, y-.10))
    sand = np.minimum(np.minimum(upper, lower), stream)
    distances = np.stack([metal, shell, sand], axis=1)
    materials = distances.argmin(axis=1)
    return distances.min(axis=1), materials

xx, yy = np.meshgrid(np.linspace(-2.08,2.08,COLS), np.linspace(2.04,-2.04,ROWS))
camera = np.array([3.0,1.6,7.0]); camera /= np.linalg.norm(camera)
right = np.cross([0,1,0], camera); right /= np.linalg.norm(right)
up = np.cross(camera, right)
origins = xx.reshape(-1,1)*right + yy.reshape(-1,1)*up + camera*7
direction = -camera
t = np.zeros(COLS*ROWS)
hit = np.zeros(COLS*ROWS,dtype=bool)
for _ in range(200):
    distance, material = scene(origins+t[:,None]*direction)
    hit |= distance < .002
    active = (~hit)&(t<12)
    if not active.any(): break
    t[active] += np.maximum(distance[active]*.65,.001)

p = origins+t[:,None]*direction
normals = np.stack([scene(p+np.eye(3)[a]*.001)[0]-scene(p-np.eye(3)[a]*.001)[0] for a in range(3)],axis=1)
normals /= np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-8)
light = np.array([-3,5,6]); light=light/np.linalg.norm(light)
diffuse = np.maximum(normals@light,0)
half = light+camera; half/=np.linalg.norm(half)
spec = np.maximum(normals@half,0)**24
brightness = .15+.64*diffuse+.65*spec
material = scene(p)[1]
brightness[material==1] = .12+.55*diffuse[material==1]
brightness[material==2] = .32+.42*diffuse[material==2]
rng=np.random.default_rng(18)
brightness += rng.uniform(-.075,.075,len(brightness))
ramp=np.array(list(' .:-=+*#%@'))
characters=ramp[np.clip((brightness*(len(ramp)-1)).astype(int),0,len(ramp)-1)]
characters[~hit]=' '
lines=[''.join(row).rstrip() for row in characters.reshape(ROWS,COLS)]
(ROOT/'assets/hourglass.txt').write_text('\n'.join(lines).strip('\n')+'\n')

for theme,bg,fg,muted in [('dark','#000000','#ffffff','#ffffff'),('light','#ffffff','#000000','#000000')]:
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="620" viewBox="0 0 960 620" role="img" aria-labelledby="title desc">',
         '<title id="title">Domino Girl — ASCII hourglass</title>',
         '<desc id="desc">An original hourglass drawn entirely with monospaced characters, with metal rims and falling sand.</desc>',
         f'<rect width="960" height="620" fill="{bg}"/>',
         f'<g fill="{fg}" font-family="Courier New,monospace" font-size="11" xml:space="preserve">']
    for row,line in enumerate(lines):
        spans=[]
        for col,char in enumerate(line):
            if char == ' ': continue
            spans.append(f'<tspan x="{180+col*6.6:.1f}">{html.escape(char)}</tspan>')
        out.append(f'<text y="{38+row*8.55:.2f}">{"".join(spans)}</text>')
    out+=['</g>',f'<text x="480" y="554" text-anchor="middle" fill="{fg}" font-family="Courier New,monospace" font-size="23" letter-spacing="7">Domino Girl</text>',
          f'<text x="480" y="584" text-anchor="middle" fill="{muted}" font-family="Courier New,monospace" font-size="11" letter-spacing="3">DATA / TOOLS / AI / MARKETING</text>','</svg>']
    (ROOT/f'assets/hourglass-{theme}.svg').write_text('\n'.join(out)+'\n')
print('Generated dark/light SVG headers and a plain-text ASCII source.')

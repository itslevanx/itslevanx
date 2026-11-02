#!/usr/bin/env python3
"""Genera el banner SVG del perfil con retratos tramados y partículas animadas.

Desde la raíz: python scripts/banner/generate.py
Dependencias: python -m pip install -r scripts/banner/requirements.txt
"""
from __future__ import annotations

import html
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('profile.json')
W, H = 1180, 610
GRID = (330, 360)
PARTICLES = 1400
HOLD, TRANSITION = 3.6, 2.2
FRAGMENTS = 48
FONT = 'ui-monospace,SFMono-Regular,Consolas,monospace'
THEMES = {
    'dark': dict(bg='#080F1D', panel='#0D1729', inset='#101D32', line='#263752',
                 text='#EDF3FF', muted='#93A6C2', accent='#59DBED', secondary='#B9AAF0'),
    'light': dict(bg='#EDF3FA', panel='#FFFFFF', inset='#F4F7FC', line='#CDD9EA',
                  text='#17263F', muted='#526984', accent='#087C94', secondary='#7051AA'),
}


def esc(value):
    return html.escape(str(value), quote=True)


def dither(gray):
    """Difusión Floyd–Steinberg serpentina de un bit por píxel."""
    values = np.asarray(gray, dtype=np.float32) / 255
    result = np.zeros(values.shape, dtype=bool)
    height, width = values.shape
    for y in range(height):
        direction = 1 if y % 2 == 0 else -1
        for x in (range(width) if direction == 1 else range(width - 1, -1, -1)):
            old = values[y, x]
            new = float(old >= .5)
            result[y, x] = bool(new)
            error = old - new
            nx = x + direction
            if 0 <= nx < width:
                values[y, nx] += error * 7 / 16
            if y + 1 < height:
                if 0 <= x - direction < width:
                    values[y + 1, x - direction] += error * 3 / 16
                values[y + 1, x] += error * 5 / 16
                if 0 <= nx < width:
                    values[y + 1, nx] += error * 1 / 16
    return result


def prepare_image(item):
    with Image.open(ROOT / 'assets/source' / item['file']) as source:
        image = source.convert('RGBA')
    if item.get('portrait'):
        # Máscara del contorno de la foto original; conserva cabello, camisa y saco.
        # Coordenadas normalizadas para no depender de la resolución de entrada.
        outline = [(0.25,.22),(.30,.15),(.43,.10),(.60,.11),(.70,.17),
                   (.75,.27),(.72,.42),(.72,.50),(.70,.62),(.65,.72),
                   (.79,.78),(.90,.87),(.94,1),(0,1),(0,.88),(.17,.80),
                   (.27,.72),(.30,.65),(.27,.54),(.27,.42),(.24,.32)]
        mask = Image.new('L', image.size)
        ImageDraw.Draw(mask).polygon([(int(x*image.width), int(y*image.height))
                                     for x, y in outline], fill=255)
        # Elimina el gris del fondo conectado a los bordes para un contorno natural.
        rgb = np.asarray(image.convert('RGB'), dtype=np.int16)
        background = ((rgb.max(axis=2)-rgb.min(axis=2) < 22)
                      & (rgb.mean(axis=2) > 105))
        background[int(image.height*.78):] = False
        exterior = np.zeros(background.shape, dtype=bool)
        queue = deque((0,x) for x in range(image.width))
        queue.extend((y,x) for y in range(image.height)
                     for x in (0,image.width-1))
        while queue:
            y,x = queue.popleft()
            if exterior[y,x] or not background[y,x]:
                continue
            exterior[y,x] = True
            for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0 <= ny < image.height and 0 <= nx < image.width:
                    queue.append((ny,nx))
        mask = Image.fromarray(np.where(exterior,0,np.asarray(mask)).astype('uint8'))
        image.putalpha(mask)
        image = image.crop((180, 95, 1130, 1132))
    else:
        box = image.getchannel('A').getbbox()
        if box is None:
            raise ValueError(f"Imagen vacía: {item['file']}")
        image = image.crop(box)
    image.thumbnail((GRID[0] - 12, GRID[1] - 12), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', GRID)
    canvas.alpha_composite(image, ((GRID[0] - image.width)//2, (GRID[1] - image.height)//2))
    return canvas


def image_points(image, theme):
    gray = ImageOps.autocontrast(ImageOps.grayscale(image.convert('RGB')), cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.2)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
    # Evita masas sólidas en el pelo blanco de Luffy y conserva el aspecto de puntos.
    if theme == 'dark':
        gray = gray.point(lambda value: int(value*.76))
    else:
        gray = gray.point(lambda value: int(255-(255*.12+(255-value)*.64)))
    alpha = np.asarray(image.getchannel('A')) > 128
    bits = dither(gray)
    active = (bits if theme == 'dark' else ~bits) & alpha
    y, x = np.where(active)
    if len(x) < PARTICLES:
        raise ValueError('La imagen no contiene suficientes puntos visibles')
    return np.column_stack((x + 79, y + 156)).astype(np.float32)


def path_runs(points):
    """Agrupa puntos consecutivos para reducir el tamaño del SVG."""
    coords = sorted({(int(x), int(y)) for x, y in points}, key=lambda p: (p[1], p[0]))
    paths, i = [], 0
    while i < len(coords):
        start, y = coords[i]
        end = start
        i += 1
        while i < len(coords) and coords[i][1] == y and coords[i][0] == end + 1:
            end = coords[i][0]
            i += 1
        paths.append(f'M{start} {y}h{end-start+1}')
    return ''.join(paths)


def match_points(source, target):
    """Empareja regiones espaciales por bisección; evita cruces largos sin SciPy."""
    ordered = np.empty_like(target)

    def split(a, b):
        if len(a) == 1:
            ordered[a[0]] = target[b[0]]
            return
        axis = int(np.argmax(np.ptp(source[a], axis=0) + np.ptp(target[b], axis=0)))
        a = a[np.argsort(source[a, axis], kind='stable')]
        b = b[np.argsort(target[b, axis], kind='stable')]
        mid = len(a)//2
        split(a[:mid], b[:mid])
        split(a[mid:], b[mid:])

    split(np.arange(len(source)), np.arange(len(target)))
    return ordered


def timeline_key(times, duration):
    return ';'.join(f'{v/duration:.5f}'.rstrip('0').rstrip('.') or '0' for v in times)


def animation(attribute, times, values, duration, transform=False):
    tag = 'animateTransform' if transform else 'animate'
    extra = ' type="translate"' if transform else ''
    # Controla la aparición del detalle; las partículas usan sus propias curvas.
    return (f'<{tag} attributeName="{attribute}"{extra} dur="{duration:g}s" '
            f'repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{timeline_key(times,duration)}" values="{";".join(values)}"/>')


def fragment_layer(clouds, duration):
    """Desmonta y reconstruye el detalle en una onda; nunca cruza dos retratos."""
    n = len(clouds)
    out = []
    for stage, cloud in enumerate(clouds):
        # La onda diagonal agrupa granos intercalados, sin baldosas visibles.
        rng = np.random.default_rng(800+stage)
        score = ((cloud[:,0]-79)/GRID[0]*.32 +
                 (cloud[:,1]-156)/GRID[1]*.68 + rng.uniform(-.07,.07,len(cloud)))
        ranking = np.argsort(score,kind='stable')
        groups = np.array_split(ranking,FRAGMENTS)
        for index, ids in enumerate(groups):
            phase = index/(FRAGMENTS-1)
            offset = np.array([12+18*phase, -12-15*(1-phase)])
            times = [0.0]
            visible = ['1' if stage == 0 else '0']
            shifts = ['0 0']
            for transition in range(n):
                start = transition*(HOLD+TRANSITION)+HOLD
                if stage == transition:
                    # La figura sale antes de que empiece a aparecer la siguiente.
                    moments = [0,.05+phase*.10,.20+phase*.13,.44,1]
                    alpha = [1,1,.32,0,0]
                    displacement = [0,0,.45,1,1]
                elif stage == (transition+1)%n:
                    moments = [0,.58,.63+phase*.11,.84+phase*.12,1]
                    alpha = [0,0,.28,1,1]
                    displacement = [-1,-1,-.45,0,0]
                else:
                    moments = [0,1]
                    alpha = [0,0]
                    displacement = [0,0]
                for moment, opacity, movement in zip(moments,alpha,displacement):
                    times.append(start+moment*TRANSITION)
                    visible.append(f'{opacity:g}')
                    delta = offset*movement
                    shifts.append(f'{delta[0]:.1f} {delta[1]:.1f}')
            # El último valor del bucle coincide con el primero, incluso oculto.
            shifts[-1] = shifts[0]
            out.append(f'<path class="detail stage-{stage}" d="{path_runs(cloud[ids])}" '
                       f'opacity="{visible[0]}">'
                       + animation('opacity',times,visible,duration)
                       + animation('transform',times,shifts,duration,transform=True)
                       + '</path>')
    return ''.join(out)


def particle_layer(clouds, duration, theme):
    """Transporta partículas por curvas Bézier nativas con aceleración suave."""
    rng = np.random.default_rng(2026)
    n = len(clouds)
    samples = [cloud[rng.choice(len(cloud),PARTICLES,replace=False)] for cloud in clouds]
    for stage in range(1,n):
        samples[stage] = match_points(samples[stage-1],samples[stage])
    phase = rng.uniform(0,2*np.pi,PARTICLES)
    bend = np.column_stack((np.cos(phase),np.sin(phase)))
    bend *= rng.uniform(22,56,PARTICLES)[:,None]
    delays = rng.uniform(.025,.13,PARTICLES)
    finishes = rng.uniform(.86,.98,PARTICLES)
    curves, lengths = [], []
    # Las longitudes fijan las paradas de cada figura sobre la curva completa.
    u = np.linspace(0,1,129)[:,None,None]
    for stage in range(n):
        source, target = samples[stage],samples[(stage+1)%n]
        delta = target-source
        c1 = source+delta*.23+bend
        c2 = target-delta*.23+bend
        points = ((1-u)**3*source + 3*(1-u)**2*u*c1
                  + 3*(1-u)*u*u*c2 + u**3*target)
        lengths.append(np.linalg.norm(np.diff(points,axis=0),axis=2).sum(axis=0))
        curves.append((source,c1,c2,target))
    cumulative = np.vstack((np.zeros(PARTICLES),np.cumsum(lengths,axis=0)))
    cumulative /= cumulative[-1]
    fade_times, alpha = [0.0], ['0']
    for stage in range(n):
        start = stage*(HOLD+TRANSITION)+HOLD
        fade_times.extend([start,start+.22*TRANSITION,start+.77*TRANSITION,start+TRANSITION])
        alpha.extend(['0','.92','.92','0'])
    out = []
    for index in range(PARTICLES):
        times, stops, splines = [0.0], ['0'], []
        commands = [f'M{samples[0][index,0]:.1f} {samples[0][index,1]:.1f}']
        for stage,(_,c1,c2,target) in enumerate(curves):
            start = stage*(HOLD+TRANSITION)+HOLD
            times.extend([start+delays[index]*TRANSITION,
                          start+finishes[index]*TRANSITION,start+TRANSITION])
            stops.extend([f'{cumulative[stage,index]:.6f}',
                          f'{cumulative[stage+1,index]:.6f}',
                          f'{cumulative[stage+1,index]:.6f}'])
            splines.extend(['0 0 1 1','.42 0 .22 1','0 0 1 1'])
            commands.append(f'C{c1[index,0]:.1f} {c1[index,1]:.1f} '
                            f'{c2[index,0]:.1f} {c2[index,1]:.1f} '
                            f'{target[index,0]:.1f} {target[index,1]:.1f}')
        color = THEMES[theme]['secondary'] if index%7 == 0 else THEMES[theme]['accent']
        width = 1.6 if index%5 == 0 else 1.15
        # Una pequeña fracción deja una estela tenue orientada con el movimiento.
        grain = '<path d="M-4 0h3" opacity=".22"/>' if index%19 == 0 else ''
        out.append(f'<g class="traveller" stroke="{color}" stroke-linecap="round" opacity="0">'
                   f'<path d="M0 0h{width}"/>{grain}'
                   f'<animateMotion dur="{duration:g}s" repeatCount="indefinite" '
                   f'rotate="auto" calcMode="spline" path="{"".join(commands)}" '
                   f'keyTimes="{timeline_key(times,duration)}" '
                   f'keyPoints="{";".join(stops)}" keySplines="{";".join(splines)}"/>'
                   + animation('opacity',fade_times,alpha,duration) + '</g>')
    return ''.join(out)


def render(config, clouds, theme):
    t = THEMES[theme]
    n = len(clouds)
    duration = n*(HOLD+TRANSITION)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{esc(config["name"])} — Machine Learning profile</title>',
           '<desc id="desc">Animated terminal profile. Leonardo’s portrait transforms '
           'into Luffy Gear 5 and a robot reading a book. Software Engineering Student '
           'in Lima, Peru, working toward ML Engineer.</desc>',
           '<defs><clipPath id="visual-clip"><rect x="49" y="140" width="390" height="390"/></clipPath></defs>',
           '<style>@media (prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}'
           '@media (prefers-reduced-motion:no-preference){.still{display:none}}</style>',
           f'<rect width="{W}" height="{H}" rx="20" fill="{t["bg"]}"/>',
           f'<rect x="13" y="13" width="1154" height="584" rx="14" fill="{t["panel"]}" stroke="{t["line"]}"/>',
           f'<path d="M13 62H1167" stroke="{t["line"]}"/>']
    for x, color in [(38,'#FF6058'), (59,'#FEBC2E'), (80,'#28C840')]:
        out.append(f'<circle cx="{x}" cy="38" r="6" fill="{color}"/>')

    def text(x, y, value, color='muted', size=12, extra=''):
        return (f'<text x="{x}" y="{y}" fill="{t[color]}" font-family="{FONT}" '
                f'font-size="{size}" {extra}>{esc(value)}</text>')

    out.append(text(590,43,'vim profile.yml',size=13,extra='text-anchor="middle" letter-spacing=".5"'))
    for x, width in [(35,418), (474,672)]:
        out.append(f'<rect x="{x}" y="88" width="{width}" height="472" rx="7" fill="{t["inset"]}" stroke="{t["line"]}"/>')
        out.append(f'<path d="M{x} 124h{width}" stroke="{t["line"]}"/>')
    out.extend([text(50,111,'VISUAL.MAP','secondary',13,'font-weight="700" letter-spacing="1"'),
                text(437,111,'330×360 / 1-BIT',size=10,extra='text-anchor="end"'),
                text(490,111,'profile.yml','secondary',13,'font-weight="700"'),
                text(591,111,'[YAML]',size=10),
                f'<rect x="1003" y="95" width="125" height="23" rx="11.5" fill="{t["secondary"]}" opacity=".14"/>',
                text(1065,111,'@'+config['username'],'secondary',12,'text-anchor="middle" font-weight="700"'),
                f'<path d="M51 143h12M51 143v12M437 143h-12M437 143v12M51 526h12M51 526v-12M437 526h-12M437 526v-12" stroke="{t["secondary"]}" opacity=".6"/>'])
    out.append(f'<g clip-path="url(#visual-clip)" fill="none" stroke="{t["accent"]}" stroke-width="1.05">')
    out.append(f'<path class="still" d="{path_runs(clouds[0])}"/>')
    out.append('<g class="motion">')
    out.append(fragment_layer(clouds,duration))
    out.append(particle_layer(clouds,duration,theme))
    out.append('</g></g>')
    out.append(text(51,548,'PORTRAIT  →  GEAR 5  →  AI','muted',10))
    rows = [(0,'profile',''),(1,'subject',config['name']),(1,'role',config['role']),
            (1,'origin',config['origin']),(1,'goal',config['goal']),(1,'focus',config['focus']),
            (0,'stack','')]
    rows.extend((1,key,value) for key,value in config['stack'].items())
    for index,(indent,key,value) in enumerate(rows,1):
        y = 153+(index-1)*25
        out.append(text(507,y,str(index),size=12,extra='text-anchor="end" opacity=".5"'))
        x = 541 if indent else 525
        out.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="13">'
                   f'<tspan fill="{t["accent"] if indent else t["secondary"]}"'
                   f' font-weight="{400 if indent else 700}">{esc(key)}:</tspan>'
                   f'<tspan fill="{t["text"]}">{" " + esc(value) if value else ""}</tspan></text>')
    out.extend([f'<path d="M474 526h672" stroke="{t["line"]}"/>',
                f'<rect x="485" y="534" width="72" height="18" rx="3" fill="{t["accent"]}"/>',
                text(521,547,'NORMAL','bg',10,'text-anchor="middle" font-weight="700"'),
                text(569,547,'profile.yml','text',11),text(735,547,'[utf-8]',size=10),
                text(1131,547,f'{len(rows)}L  ·  100%','muted',10,'text-anchor="end"'),
                '</svg>'])
    return ''.join(out)


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    images = [prepare_image(item) for item in config['sequence']]
    for theme in THEMES:
        clouds = [image_points(image,theme) for image in images]
        output = ROOT / 'assets' / f'profile-banner-{theme}.svg'
        output.write_text(render(config,clouds,theme),encoding='utf-8')
        print(f'{output.relative_to(ROOT)}: {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()

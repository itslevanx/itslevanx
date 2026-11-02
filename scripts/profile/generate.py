#!/usr/bin/env python3
"""Genera Skills y el cierre del README con iconos locales y rutas versionadas."""
from pathlib import Path
import hashlib
import html
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ICONS = Path(__file__).with_name('icons')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
GROUPS = [
    ('languages', 'Languages', [('python','Python'),('swift','Swift'),('html5','HTML5'),
                               ('css3','CSS3'),('latex','LaTeX'),('markdown','Markdown')]),
    ('machine-learning', 'Machine Learning / Data Science', [('pytorch','PyTorch'),
        ('scikitlearn','scikit-learn'),('numpy','NumPy'),('pandas','pandas'),('matplotlib','Matplotlib')]),
    ('databases', 'Databases', [('microsoftsqlserver','SQL Server'),('mysql','MySQL'),
        ('postgresql','PostgreSQL'),('sqlite','SQLite'),('supabase','Supabase')]),
    ('hosting', 'Hosting / SaaS', [('github','GitHub Pages'),('render','Render')]),
    ('editors', 'IDEs / Editors', [('devin','Devin'),('googlecolab','Google Colab'),
        ('notepadplusplus','Notepad++'),('visualstudio','Visual Studio'),
        ('vscode','VS Code'),('xcode','Xcode')]),
    ('tools', 'Other Tools & Technologies', [('git','Git'),('n8n','n8n')]),
]
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif'


def icon(key, x, y):
    if key == 'devin':
        return (f'<text x="{x+18}" y="{y+29}" text-anchor="middle" '
                'class="ink" font-size="32" font-weight="650">D</text>')
    root = ET.fromstring((ICONS/f'{key}.svg').read_text())
    for attribute in ('id','width','height','x','y'):
        root.attrib.pop(attribute,None)
    root.set('x',str(x))
    root.set('y',str(y))
    root.set('width','36')
    root.set('height','36')
    root.set('aria-hidden','true')
    # Prefijos únicos para que gradientes y referencias no colisionen entre logos.
    for node in root.iter():
        if 'id' in node.attrib:
            node.set('id',key+'-'+node.get('id'))
        for attr,value in list(node.attrib.items()):
            value = re.sub(r'url\(#([^)]*)\)',lambda m:f'url(#{key}-{m[1]})',value)
            if attr.endswith('href') and value.startswith('#'):
                value = '#'+key+'-'+value[1:]
            node.set(attr,value)
    # Los símbolos monocromáticos mantienen contraste en los dos temas.
    mono = {'latex','markdown','github','render','pandas','notepadplusplus'}
    if key in mono:
        for node in root.iter():
            node.attrib.pop('color',None)
            if node.tag.rsplit('}',1)[-1] in {'path','rect','polygon','circle','ellipse'}:
                if node.get('fill') != 'none':
                    node.set('fill','currentColor')
                node.attrib.pop('style',None)
        root.set('class','ink')
    if key == 'n8n':
        root.set('fill','#EA6D8D')
    return ET.tostring(root,encoding='unicode')


def strip(title, items):
    width = len(items)*112
    out = [f'<svg xmlns="{NS}" width="{width}" height="100" '
           f'viewBox="0 0 {width} 100" role="img" aria-labelledby="title" font-family="{FONT}">',
           f'<title id="title">{html.escape(title)}: {html.escape(", ".join(label for _,label in items))}</title>',
           '<style>.label{fill:#B5C2D6}.tile{fill:#111C2E;stroke:#26354B}'
           '.ink{color:#CBD5E6;fill:#CBD5E6}'
           '@media(prefers-color-scheme:light){.label{fill:#40536D}'
           '.tile{fill:#F6F8FC;stroke:#DCE4EF}.ink{color:#334765;fill:#334765}}</style>']
    for index,(key,label) in enumerate(items):
        center = 56+112*index
        out.append(f'<rect class="tile" x="{center-27}" y="6" width="54" height="54" rx="15"/>')
        out.append(icon(key,center-18,15))
        out.append(f'<text class="label" x="{center}" y="83" text-anchor="middle" '
                   f'font-size="12" font-weight="500">{html.escape(label)}</text>')
    out.append('</svg>')
    return ''.join(out)


def footer(theme,compact=False):
    colors = {'dark':('#E5EDF8','#8C9CB3','#28374E','#59DBED'),
              'light':('#182C48','#586D88','#D9E2EE','#087C94')}
    ink,muted,line,accent = colors[theme]
    if compact:
        return f'''<svg xmlns="{NS}" width="420" height="180" viewBox="0 0 420 180" role="img" aria-labelledby="title desc" font-family="{FONT}">
<title id="title">Thanks for stopping by.</title>
<desc id="desc">Leonardo Sullón. Always learning, always building, always exploring.</desc>
<path d="M24 18H189M231 18H396" stroke="{line}"/>
<path d="M210 13l5 5-5 5-5-5z" fill="none" stroke="{accent}" stroke-width="1.3"/>
<text x="210" y="72" text-anchor="middle" fill="{ink}" font-size="26" font-weight="600" letter-spacing="-.6">Thanks for stopping by.</text>
<text x="210" y="104" text-anchor="middle" fill="{muted}" font-size="14">Always learning · Always building</text>
<text x="210" y="125" text-anchor="middle" fill="{muted}" font-size="14">Always exploring</text>
<text x="210" y="160" text-anchor="middle" fill="{muted}" font-size="10" font-weight="500" letter-spacing="2">LEONARDO SULLÓN</text>
</svg>'''
    return f'''<svg xmlns="{NS}" width="880" height="170" viewBox="0 0 880 170" role="img" aria-labelledby="title desc" font-family="{FONT}">
<title id="title">Thanks for stopping by.</title>
<desc id="desc">Leonardo Sullón. Always learning, always building, always exploring.</desc>
<path d="M100 18H419M461 18H780" stroke="{line}"/>
<path d="M440 13l5 5-5 5-5-5z" fill="none" stroke="{accent}" stroke-width="1.3"/>
<text x="440" y="76" text-anchor="middle" fill="{ink}" font-size="27" font-weight="600" letter-spacing="-.6">Thanks for stopping by.</text>
<text x="440" y="106" text-anchor="middle" fill="{muted}" font-size="13">Always learning · Always building · Always exploring</text>
<text x="440" y="145" text-anchor="middle" fill="{muted}" font-size="10" font-weight="500" letter-spacing="2.5">LEONARDO SULLÓN</text>
</svg>'''


def save(stem,svg):
    revision = hashlib.sha256(svg.encode()).hexdigest()[:10]
    output = ROOT/'assets'/f'{stem}.{revision}.svg'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(svg,encoding='utf-8')
    for old in output.parent.glob(output.stem.rsplit('.',1)[0]+'.*.svg'):
        if old != output and re.fullmatch(re.escape(Path(stem).name)+r'\.[a-f0-9]{10}\.svg',old.name):
            old.unlink()
    return './'+str(output.relative_to(ROOT))


def main():
    readme_path = ROOT/'README.md'
    readme = readme_path.read_text()
    parts = ['## Skills','', '<div align="center">', '']
    for key,title,items in GROUPS:
        images = []
        # Filas de hasta tres iconos: juntas en escritorio y centradas al envolver
        # en pantallas pequeñas, sin reducir los nombres a tamaños ilegibles.
        for row,start in enumerate(range(0,len(items),3),1):
            subset = items[start:start+3]
            path = save(f'skills/{key}-{row}',strip(title,subset))
            names = ', '.join(label for _,label in subset)
            images.append(f'<img src="{path}" width="{len(subset)*112}" alt="{html.escape(names)}" />')
        parts.extend([f'<h4>{html.escape(title)}</h4>', '',
                      '<p>\n'+'\n'.join(images)+'\n</p>', ''])
    parts.extend(['</div>','','<div align="center">',''])
    start,end = readme.index('## Skills'),readme.index('## Certifications')
    readme = readme[:start]+'\n'.join(parts)+'\n'+readme[end:]
    dark,light = (save('footer-'+theme,footer(theme)) for theme in ('dark','light'))
    compact_dark,compact_light = (save('footer-'+theme+'-compact',footer(theme,compact=True))
                                  for theme in ('dark','light'))
    picture = ('<picture>\n'
               f'  <source media="(max-width: 540px) and (prefers-color-scheme: dark)" srcset="{compact_dark}" />\n'
               f'  <source media="(max-width: 540px) and (prefers-color-scheme: light)" srcset="{compact_light}" />\n'
               f'  <source media="(prefers-color-scheme: dark)" srcset="{dark}" />\n'
               f'  <source media="(prefers-color-scheme: light)" srcset="{light}" />\n'
               f'  <img src="{dark}" width="100%" alt="Thanks for stopping by — Leonardo Sullón. Always learning, always building, always exploring." />\n'
               '</picture>')
    pattern = r'<picture>\s*<source[^>]*srcset="\./assets/footer-[^\"]+".*?</picture>|<img[^>]*src="\./assets/footer\.svg"[^>]*>'
    readme,count = re.subn(pattern,lambda _:picture,readme,flags=re.S)
    if count != 1:
        raise ValueError('No se encontró un único cierre de agradecimiento')
    readme_path.write_text(readme,encoding='utf-8')
    print('Skills: 6 categorías, 26 herramientas; cierre claro y oscuro generados.')


if __name__ == '__main__':
    main()

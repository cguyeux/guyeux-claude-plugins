#!/usr/bin/env python3
"""P11.6 — a standalone local browser: tree <-> markers <-> strains, three linked views.

Our figures (`itol`, `sci-figure`) are static and one-directional. Nothing in the
toolbox supports the everyday gesture of manual taxonomic work: "what does this
clade rest on? what does this marker define?". This writes a single HTML file,
openable over `file://`, data embedded, no dependency and no framework.

Three views, linked both ways:
  1. the laminar tree (clades, nested)
  2. the profile x marker heatmap in three states (ON / OFF / UNKNOWN)
  3. the marker x marker relation matrix (five codes)
Clicking a clade highlights ITS markers in both matrices; clicking a marker
column highlights the clade it defines.

SCALE IS THE CONSTRAINT, and it is not negotiable. The grid is painted once into
an `ImageData` at one pixel per cell, then scaled by the canvas, which stays fluid
at several hundred thousand cells. On RAW strains (35 401 rows for L2.2.1) that
image is out of reach. One never browses the raw matrix, one browses the REDUCED
matrix, and our deduplicated profiles are its natural rows.
"""

from __future__ import annotations

import base64
import json

# ON / OFF / UNKNOWN are 1 / 0 / 2; relation codes are those of RelationMask
_CSS = """
:root{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6b6b66;--line:#d8d8d3;--accent:#8a5a2b;--panel:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#16161a;--fg:#e8e8e4;
--mut:#9a9a94;--line:#33333a;--accent:#d9a066;--panel:#1e1e24}}
*{box-sizing:border-box}
body{margin:0;font:13px/1.5 ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:.7rem 1rem;border-bottom:1px solid var(--line);display:flex;gap:1.2rem;
align-items:baseline;flex-wrap:wrap}
h1{font-size:14px;margin:0;font-weight:600}
.meta{color:var(--mut);font-size:12px}
main{display:grid;grid-template-columns:minmax(230px,300px) 1fr;gap:0;height:calc(100vh - 52px)}
#tree{overflow:auto;border-right:1px solid var(--line);padding:.5rem}
#right{display:grid;grid-template-rows:1fr 1fr;overflow:hidden}
section{overflow:hidden;display:flex;flex-direction:column;border-bottom:1px solid var(--line)}
.hd{padding:.35rem .7rem;font-size:11px;color:var(--mut);text-transform:uppercase;
letter-spacing:.06em;border-bottom:1px solid var(--line);display:flex;gap:.8rem;flex-wrap:wrap}
canvas{flex:1;min-height:0;width:100%;image-rendering:pixelated;cursor:crosshair}
.node{padding:1px 4px;border-radius:3px;cursor:pointer;white-space:nowrap;font-size:12px}
.node:hover{background:var(--line)}
.node.sel{background:var(--accent);color:var(--bg)}
.sw{display:inline-block;width:9px;height:9px;border-radius:2px;vertical-align:-1px;
margin-right:3px;border:1px solid rgba(128,128,128,.35)}
#info{position:fixed;right:.6rem;bottom:.6rem;max-width:min(460px,46vw);background:var(--panel);
border:1px solid var(--line);border-radius:6px;padding:.6rem .75rem;font-size:12px;
box-shadow:0 2px 14px rgba(0,0,0,.13);display:none}
#info code{font-size:11px;word-break:break-all}
"""

_JS = r"""
const D = window.__DATA__;
const dec = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const STATE = dec(D.state), REL = dec(D.rel);
const nP = D.n_profiles, nM = D.n_markers;
// three-state palette, then the five relation codes
const CS = {0:[236,236,232],1:[38,70,110],2:[214,190,150]};
const CR = {0:[150,150,150],1:[70,120,180],2:[70,150,120],3:[240,240,236],4:[200,70,60]};
let sel = null;                       // selected clade index, or null

function paint(cv, w, h, get){
  const ctx = cv.getContext('2d');
  cv.width = w; cv.height = h;
  const img = ctx.createImageData(w, h), d = img.data;
  for (let y=0, p=0; y<h; y++) for (let x=0; x<w; x++, p+=4){
    const c = get(x, y);
    d[p]=c[0]; d[p+1]=c[1]; d[p+2]=c[2]; d[p+3]=255;
  }
  ctx.putImageData(img, 0, 0);
}

function highlightSet(){
  if (sel === null) return null;
  return new Set(D.clade_markers[sel]);      // marker indices defining this clade
}

function draw(){
  const hl = highlightSet();
  const rows = sel === null ? null : new Set(D.clade_rows[sel]);
  paint(document.getElementById('heat'), nM, nP, (x,y) => {
    const c = CS[STATE[y*nM + x]];
    if (hl && hl.has(x)) return [Math.min(255,c[0]+60), c[1], Math.max(0,c[2]-40)];
    if (rows && rows.has(y)) return [c[0], Math.min(255,c[1]+35), c[2]];
    return c;
  });
  paint(document.getElementById('relm'), nM, nM, (x,y) => {
    const c = CR[REL[y*nM + x]];
    if (hl && (hl.has(x) || hl.has(y))) return [Math.min(255,c[0]+55), c[1], Math.max(0,c[2]-30)];
    return c;
  });
}

function showInfo(html){
  const el = document.getElementById('info');
  el.innerHTML = html; el.style.display = 'block';
}

function pickClade(i){
  sel = (sel === i) ? null : i;
  document.querySelectorAll('.node').forEach(n =>
    n.classList.toggle('sel', sel !== null && +n.dataset.i === sel));
  draw();
  if (sel === null){ document.getElementById('info').style.display='none'; return; }
  const mk = D.clade_markers[sel].map(j => D.markers[j]);
  showInfo(`<b>clade ${sel}</b> — ${D.clade_rows[sel].length} profiles, `
    + `${D.clade_weight[sel]} strains<br><span class="meta">rests on `
    + `${mk.length} marker${mk.length>1?'s':''}</span><br><code>`
    + mk.slice(0,14).join('<br>') + (mk.length>14 ? `<br>… +${mk.length-14}` : '') + `</code>`);
}

function markerAt(cv, ev, n){
  const r = cv.getBoundingClientRect();
  return Math.min(n-1, Math.max(0, Math.floor((ev.clientX - r.left) / r.width * n)));
}

window.addEventListener('DOMContentLoaded', () => {
  const tree = document.getElementById('tree');
  D.tree_order.forEach(({i, depth}) => {
    const el = document.createElement('div');
    el.className = 'node'; el.dataset.i = i;
    el.style.paddingLeft = (depth * 11 + 4) + 'px';
    el.textContent = `${D.clade_rows[i].length}p / ${D.clade_weight[i]}s `
                   + `· ${D.clade_markers[i].length} mk`;
    el.title = D.clade_markers[i].slice(0,4).join('  ');
    el.onclick = () => pickClade(i);
    tree.appendChild(el);
  });

  const heat = document.getElementById('heat');
  heat.onclick = ev => {
    const j = markerAt(heat, ev, nM);
    const owner = D.marker_clade[j];
    showInfo(`<b>${D.markers[j]}</b><br><span class="meta">present in `
      + `${D.marker_size[j]} profiles · class ${D.marker_class[j]}</span>`
      + (owner >= 0 ? `<br>defines clade ${owner}` : `<br>defines no laminar clade`));
    if (owner >= 0) pickClade(owner);
  };
  draw();
});
"""


def _b64(arr):
    return base64.b64encode(arr.astype("uint8").tobytes()).decode("ascii")


def write_browser(path, *, state, rel, markers, marker_class, marker_size, marker_clade,
                  clade_rows, clade_markers, clade_weight, tree_order, title, subtitle):
    """Write the standalone HTML. `state` is (n_profiles, n_markers) of 0/1/2."""
    data = {
        "n_profiles": int(state.shape[0]),
        "n_markers": int(state.shape[1]),
        "state": _b64(state),
        "rel": _b64(rel),
        "markers": list(markers),
        "marker_class": list(marker_class),
        "marker_size": [int(x) for x in marker_size],
        "marker_clade": [int(x) for x in marker_clade],
        "clade_rows": [[int(x) for x in r] for r in clade_rows],
        "clade_markers": [[int(x) for x in m] for m in clade_markers],
        "clade_weight": [int(x) for x in clade_weight],
        "tree_order": tree_order,
    }
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{_CSS}</style></head><body>
<header>
  <h1>{title}</h1>
  <span class="meta">{subtitle}</span>
  <span class="meta"><span class="sw" style="background:#26466e"></span>ON
  <span class="sw" style="background:#ececE8"></span>OFF
  <span class="sw" style="background:#d6be96"></span>UNKNOWN</span>
  <span class="meta"><span class="sw" style="background:#c8463c"></span>crossing
  <span class="sw" style="background:#4678b4"></span>nested
  <span class="sw" style="background:#469678"></span>equal
  <span class="sw" style="background:#f0f0ec"></span>disjoint</span>
</header>
<main>
  <div id="tree"></div>
  <div id="right">
    <section><div class="hd">profiles &times; markers (three states) — click a column</div>
      <canvas id="heat"></canvas></section>
    <section><div class="hd">marker &times; marker relations</div>
      <canvas id="relm"></canvas></section>
  </div>
</main>
<div id="info"></div>
<script>window.__DATA__ = {json.dumps(data, separators=(",", ":"))};</script>
<script>{_JS}</script>
</body></html>
"""
    path.write_text(html)
    return path

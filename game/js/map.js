/* The campaign map: a 1942 navy chart of the Pacific drawn as SVG, with a brass pin for each mission.
   Coastlines are simplified by hand from real coordinates (longitude 110°E to 150°W, latitude 55°N to 25°S). */
(function () {
const SC = window.SC, UI = SC.UI, {$, esc} = UI;
const P = (lon, lat) => [Math.round((lon - 110) * 100) / 10, Math.round((55 - lat) * 100) / 10];
const poly = pts => 'M' + pts.map(([a, b]) => P(a, b).join(' ')).join(' L') + ' Z';
const LAND = [
  [[110,55],[137,55],[141,52],[140,48],[138,46],[135,43],[131,42.5],[129.5,40],[128.5,38.5],[129.4,36],[129,35.1],[126.5,34.4],[126.2,36.5],[124.7,38],[125,39.7],[121.5,39],[122,40.5],[119,39.5],[118,38.6],[121,37.5],[122.5,37],[120.3,36],[119.5,35],[121,32],[121.9,30.8],[121.5,28.5],[119.5,25.5],[117,23.5],[114,22.3],[111,21.5],[110,20]],
  [[155.6,55],[156,51],[158,52.5],[160,54],[161.5,55]],
  [[140,41.5],[141.2,41.8],[143.2,42],[145.5,43.3],[144,44.3],[141.7,45.4],[141.2,43.5],[140.2,42.8]],
  [[141.5,41.3],[142,39.5],[141,38.3],[140.9,36.9],[140.8,35.7],[139.8,35],[138.8,34.6],[137,34.6],[135.7,33.5],[135,34.6],[133,34.3],[131,34],[130.9,34.4],[132,35.4],[133.5,35.5],[135.8,35.6],[136.8,37.2],[137.4,36.8],[139,37.9],[140,39.5],[140,40.8]],
  [[130,33.8],[131,33.9],[131.8,33.2],[131.5,31.5],[130.6,31],[130.2,32.2],[129.6,33.2]],
  [[132.5,33.9],[134.3,34.2],[134.7,33.8],[133.7,33.4],[132.9,32.8],[132.5,33.3]],
  [[120.1,23],[120.9,22],[121.9,24.6],[121.5,25.3],[120.7,24.6]],
  [[120.6,18.5],[122.3,18.5],[122.1,16.2],[121.5,15],[122.5,14],[124.2,13],[123.3,12.7],[122.5,13.5],[121.4,13.8],[120.6,14.4],[120,16]],
  [[122,7],[124,8.5],[125.5,9.5],[126.5,8],[126,6.3],[125.4,5.6],[124,6.5],[122.1,6.9]],
  [[122.5,11.8],[124.3,11.5],[125,10.5],[124,10],[123,10.5],[122.1,10.7]],
  [[117.2,8.4],[119.4,10.6],[119.7,11.3],[118.7,10.3]],
  [[110,1.6],[111.5,2.8],[113,3.2],[115.5,5.2],[116.8,7],[118.5,5.6],[119.2,5],[118,4.4],[118.5,1],[117.8,.5],[117.5,-.8],[116.5,-2.5],[116,-3.8],[114.5,-3.6],[113,-3],[111.5,-3],[110.2,-2.8],[110,-1]],
  [[119.3,-5.5],[120.4,-5.6],[120.6,-2.6],[121.6,-4.6],[123,-4.3],[122,-1.5],[121.5,-1],[123.3,-.8],[125,1.5],[124.3,1],[120.5,.4],[119.7,-.3],[119,-3.5]],
  [[110,-6.8],[112.5,-6.9],[114.5,-7.7],[114.3,-8.6],[110,-8.1]],
  [[124,-9.2],[127.2,-8.3],[125,-9.5],[123.5,-10.3]],
  [[131,-1.3],[132.5,-.4],[134,-.9],[135,-3.3],[137.8,-1.5],[141,-2.6],[144.5,-3.8],[146,-5.6],[147.5,-6.2],[148,-8],[150,-10.3],[147.5,-10.1],[146,-8.6],[144,-7.7],[143,-9],[141,-9.2],[139,-8.1],[138,-8.4],[137.6,-5.2],[135,-4.4],[133,-4],[132,-2.8]],
  [[148.5,-5.5],[150,-5],[151.5,-4.2],[152.3,-4.2],[152,-5.5],[150.5,-6.2],[149,-6.1]],
  [[150.8,-2.6],[152.3,-3.6],[153,-4.7],[152.6,-4.4],[151,-3]],
  [[154.6,-5],[155.9,-6.6],[155.2,-6.9],[154.5,-5.6]],
  [[159.6,-9.3],[160.8,-9.8],[160.4,-9.9],[159.7,-9.8]],
  [[113.5,-22],[114.2,-21.8],[116.5,-20.7],[119,-19.9],[121.5,-18.5],[122.3,-17],[124,-16.3],[125.5,-14.5],[127,-13.8],[129.5,-14.9],[130,-13],[132,-11.3],[133,-11.6],[135.5,-12],[136.9,-12.2],[136,-13.6],[135.5,-15],[137.5,-16.2],[139.2,-17.4],[140.8,-17.4],[141.6,-15.2],[141.6,-12.5],[142.5,-10.7],[143.3,-12.8],[143.8,-14.4],[145.3,-15],[146,-17.5],[147,-19.2],[149,-20.5],[150.8,-22.6],[153,-25],[153.5,-28],[113.5,-28]],
  [[193.5,55],[196.5,54.5],[198,55]],
];
const ISLES = [[200.5,22.05,.35],[202,21.45,.4],[203,21.15,.25],[203.7,20.8,.4],[204.6,19.6,.9],[144.8,13.4,.25],[173,1.4,.2],[166.6,19.3,.18],[167.7,9.2,.22],[171.4,7.1,.18],[151.8,7.4,.3],[145.7,15.2,.22]]
  .concat([[172.9,52.9],[174,52.5],[177.5,51.9],[180.5,51.7],[183.5,51.8],[186,52],[188,52.2],[190,52.6],[192,53],[193.5,53.4],[195,54]].map(([a, b]) => [a, b, .3]));
const LABELS = [[175, 12, 'PACIFIC OCEAN', 26, 6], [156, -16, 'CORAL SEA', 16, 3], [128, 26, 'East China Sea', 13, 1], [123, -21, 'AUSTRALIA', 15, 3], [114, 47, 'CHINA', 15, 3], [139, -5.8, 'New Guinea', 13, 1], [137, 37.5, 'JAPAN', 13, 2]];

let base = null;
function baseSvg(){
  if (base) return base;
  const grid = [];
  for (let lon = 120; lon <= 200; lon += 10) { const [x] = P(lon, 0); grid.push(`<path d="M${x} 0 V800" class="gl"/><text x="${x + 4}" y="794" class="gt">${lon <= 180 ? lon + '°E' : (360 - lon) + '°W'}</text>`); }
  for (let lat = 50; lat >= -20; lat -= 10) { const [, y] = P(0, lat); grid.push(`<path d="M0 ${y} H1000" class="gl ${lat === 0 ? 'eq' : ''}"/><text x="6" y="${y - 4}" class="gt">${lat === 0 ? 'Equator' : Math.abs(lat) + '°' + (lat > 0 ? 'N' : 'S')}</text>`); }
  base = `<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0 V6" stroke="#cdbb8e" stroke-width="1.2"/></pattern>
    <radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#4a3a1a" stop-opacity=".28"/></radialGradient></defs>
    <style>.sea{fill:#cfe0de}.gl{stroke:#9fbcbc;stroke-width:1;opacity:.6}.gl.eq{stroke:#7fa5a5;stroke-dasharray:6 5;opacity:.9}.gt{font:12px 'Typewriter',monospace;fill:#6f9090}
      .land{fill:#ecdfba;stroke:#a68c5c;stroke-width:1.6;stroke-linejoin:round}.land2{fill:url(#hatch)}.isle{fill:#ecdfba;stroke:#a68c5c;stroke-width:1.4}
      .lab{font-family:'Typewriter',monospace;fill:#6d5a38;text-anchor:middle}.place{font:14px 'Typewriter',monospace;fill:#3d3220}.dot{fill:#3d3220}
      .route{fill:none;stroke:#c9402f;stroke-width:3;stroke-dasharray:2 9;stroke-linecap:round;opacity:.75}</style>
    <rect class="sea" width="1000" height="800"/>${grid.join('')}
    ${LAND.map(l => `<path class="land" d="${poly(l)}"/><path class="land2" d="${poly(l)}" opacity=".35"/>`).join('')}
    ${ISLES.map(([a, b, r]) => { const [x, y] = P(a, b); return `<circle class="isle" cx="${x}" cy="${y}" r="${Math.max(2.4, r * 10)}"/>`; }).join('')}
    ${LABELS.map(([a, b, t, sz, ls]) => { const [x, y] = P(a, b); return `<text class="lab" x="${x}" y="${y}" style="font-size:${sz}px;letter-spacing:${ls}px">${t}</text>`; }).join('')}
    ${Object.entries(SC.PLACES).filter(([k]) => k !== 'luck').map(([, [a, b, name]]) => { const [x, y] = P(a, b), left = a > 196;
      return `<circle class="dot" cx="${x}" cy="${y}" r="3.5"/><text class="place" x="${left ? x - 8 : x + 8}" y="${y - 6}" text-anchor="${left ? 'end' : 'start'}">${name}</text>`; }).join('')}
    ${compass(915, 700)}<rect width="1000" height="800" fill="url(#vig)" pointer-events="none"/>`;
  return base;
}
function compass(x, y){
  return `<g transform="translate(${x} ${y})" opacity=".8"><circle r="38" fill="none" stroke="#a68c5c" stroke-width="1.5"/><circle r="30" fill="none" stroke="#a68c5c" stroke-width=".8"/>
    <path d="M0 -44 L7 0 L0 44 L-7 0 Z" fill="#6d5a38"/><path d="M-44 0 L0 7 L44 0 L0 -7 Z" fill="#a68c5c"/><path d="M0 -44 L7 0 L-7 0 Z" fill="#c9402f"/>
    <text y="-50" text-anchor="middle" style="font:15px 'Stencil',sans-serif;fill:#6d5a38">N</text></g>`;
}
const pinXY = id => { const [a, b] = SC.PLACES[id]; return P(a, b); };

SC.Map = {
  P, mini(pin){ const [x, y] = pinXY(pin);
    const vx = Math.max(0, Math.min(1000 - 320, x - 160)), vy = Math.max(0, Math.min(800 - 240, y - 120));
    return `<svg viewBox="${vx} ${vy} 320 240">${baseSvg()}<circle cx="${x}" cy="${y}" r="13" fill="none" stroke="#c9402f" stroke-width="4"/><circle cx="${x}" cy="${y}" r="5" fill="#c9402f"/></svg>`; },
  render(){
    const p = SC.Store.current(), c = SC.CAMPAIGNS[0];
    $('campTitle').textContent = c.title; $('campSub').textContent = `${c.sub} · ${c.office}`;
    $('mapMe').innerHTML = p ? `${UI.avatar(p, 'sm')}<span>${esc(p.name)}</span>` : '';
    const pts = c.missions.map(m => pinXY(m.pin));
    const route = `<path class="route" d="M${pts.map(q => q.join(' ')).join(' L')}"/>`;
    const pins = c.missions.map((m, i) => { const [x, y] = pts[i], open = SC.missionOpen(p, c, i), rec = (p && p.missions[m.id]) || {}, next = open && !rec.done;
      return `<g class="pin ${open ? '' : 'locked'}" data-mid="${m.id}" transform="translate(${x} ${y - (i === 3 ? 0 : 0)})" tabindex="${open ? 0 : -1}" role="button" aria-label="Mission ${i + 1}: ${esc(m.title)}">
        ${next ? '<circle class="halo" r="22"/>' : ''}<path d="M0 0 L0 -26" stroke="#6b4f1d" stroke-width="3"/>
        <circle class="head" cy="-34" r="15" fill="${rec.done ? '#3caf62' : open ? '#e0b94f' : '#9a8b6a'}" stroke="#6b4f1d" stroke-width="2.5"/>
        <text y="-28" text-anchor="middle" style="font:17px 'Stencil',sans-serif;fill:${rec.done ? '#fff' : '#2a1f08'}">${rec.done ? '✓' : i + 1}</text>
        ${rec.done ? `<text y="14" text-anchor="middle" style="font:14px sans-serif;fill:#b88f2c">${'★'.repeat(rec.stars)}${'☆'.repeat(3 - rec.stars)}</text>` : ''}</g>`; }).join('');
    $('chart').innerHTML = baseSvg() + route + pins;
    $('missionList').innerHTML = c.missions.map((m, i) => { const open = SC.missionOpen(p, c, i), rec = (p && p.missions[m.id]) || {};
      return `<button class="mcard ${rec.done ? 'done' : ''}" data-mid="${m.id}" ${open ? '' : 'disabled'}><span class="num">${rec.done ? '✓' : i + 1}</span>
        <span style="min-width:0"><b>${esc(m.title)}</b><small>${esc(m.date)} · ${esc(m.place)}</small></span><span class="stars">${UI.starsHtml(rec.stars || 0)}</span></button>`; }).join('')
      + `<div class="levelchip">Your level: <b>${esc(SC.LEVELS[(p || {}).level || 'codebreaker'].label)}</b> · ${esc(SC.LEVELS[(p || {}).level || 'codebreaker'].blurb)} <button class="link" id="mapLevel">Change</button></div>
         <div class="levelchip muted">${esc(c.blurb)}</div>`;
    $('mapLevel').onclick = () => UI.profileModal(p);
  },
};
const pick = e => { const b = e.target.closest('[data-mid]'); if (!b || b.disabled || b.classList.contains('locked')) return; SC.sfx.click(); SC.Game.openMission(b.dataset.mid); };
$('chart').addEventListener('click', pick); $('missionList').addEventListener('click', pick);
$('chart').addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') pick(e); });
$('mapBack').onclick = () => SC.Game.home();
})();

/* Player avatars, from Crater Crew: 32 young agents (one for every player in a full class), drawn as small SVG faces
   on the player's color, plus the mentor. p.avatar is the index; without one the profile shows its first letter.
   Spy Cadet adds 1940s hats: a navy cap, a fedora and a beret. */
(function () {
const SC = window.SC = window.SC || {};
const SKIN = {pale:'#f6dccb', light:'#efc8a8', tan:'#d9a37a', medium:'#b97b52', dark:'#8a5534', deep:'#5e3920',
  alien:'#8ed46b', robot:'#b9c2cc', violet:'#b48ce8', blue:'#7fb2e6'};
const HAIR = {black:'#1e1a1a', brown:'#5b3a24', blonde:'#e8c25a', red:'#c8502c', orange:'#ef8a2e', white:'#f2f2f2', gray:'#b8bcc2',
  green:'#4fd08a', blue:'#4b9cf0', purple:'#9a5ee0', pink:'#f26fb0', teal:'#3cc9b8'};
/* name, skin, hair style, hair color, eyes, mouth, extras */
SC.AVATARS = [
  ['Nova','medium','ponytail','black','dots','smile',['beret']],
  ['Ada','light','bob','red','glasses','smile',['freckles']],
  ['Zuri','dark','afro','black','dots','grin',['headset']],
  ['Mei','tan','buns','black','dots','smile',['blush']],
  ['Luna','pale','long','brown','dots','smile',['scarf']],
  ['Rosa','tan','curly','brown','glasses','grin',['beret']],
  ['Ivy','deep','braids','black','dots','smile',['freckles']],
  ['Prof. Cipher','light','wild','white','glasses','teeth',['bowtie']],
  ['Sky','dark','short','black','dots','grin',['cap']],
  ['Astra','medium','bob','blonde','dots','smile',['headset']],
  ['Pixel','pale','long','orange','glasses','smile',['beret']],
  ['Juno','tan','ponytail','blonde','dots','smile',['blush']],
  ['Leo','light','short','brown','dots','smile',['fedora']],
  ['Omar','medium','short','black','glasses','smile',['tie']],
  ['Kenji','tan','spiky','black','dots','grin',['headset']],
  ['Theo','pale','curly','red','dots','smile',['freckles','bowtie']],
  ['Malik','deep','buzz','black','dots','grin',['cap']],
  ['Diego','tan','short','black','dots','smile',['fedora']],
  ['Prof. Morse','light','wild','gray','dots','teeth',['brows','tache','bowtie']],
  ['Finn','light','spiky','blonde','dots','smile',['cap']],
  ['Raj','medium','short','black','monocle','smile',['bowtie']],
  ['Hazel','light','bob','brown','glasses','smile',['scarf']],
  ['Ruby','deep','curly','black','dots','grin',['beret']],
  ['Tess','pale','braids','blonde','dots','smile',['headset']],
  ['Amara','deep','buns','black','dots','smile',['scarf']],
  ['Iris','medium','long','black','dots','smile',['headset']],
  ['Tomas','tan','curly','black','glasses','smile',['tie']],
  ['Kofi','dark','afro','black','dots','grin',['headset']],
  ['Ollie','light','spiky','orange','dots','smile',['freckles','cap']],
  ['Sam','pale','short','blonde','dots','smile',['fedora']],
  ['Arjun','medium','short','black','dots','grin',['tie']],
  ['Nell','tan','ponytail','red','glasses','smile',['beret']],
  ['Lt. Marlow','light','short','brown','dots','smile',['cap','tie','uniform']],
].map(([name, skin, hair, hc, eyes, mouth, extra], i) => ({id:i, name, skin, hair, hc, eyes, mouth, extra}));

const darker = (hex, f) => '#' + hex.slice(1).match(/../g).map(h => Math.max(0, Math.round(parseInt(h, 16) * f)).toString(16).padStart(2, '0')).join('');
function hairBack(a, c){
  switch (a.hair) {
    case 'long': return `<path d="M15 32 Q14 14 32 13 Q50 14 49 32 L51 54 Q44 58 40 50 L24 50 Q20 58 13 54 Z" fill="${c}"/>`;
    case 'afro': return `<circle cx="32" cy="27" r="21" fill="${c}"/>`;
    case 'ponytail': return `<path d="M46 22 Q60 26 54 46 Q50 36 45 30 Z" fill="${c}"/>`;
    case 'braids': return `<rect x="13" y="30" width="6" height="22" rx="3" fill="${c}"/><rect x="45" y="30" width="6" height="22" rx="3" fill="${c}"/>`;
    case 'buns': return `<circle cx="17" cy="16" r="7" fill="${c}"/><circle cx="47" cy="16" r="7" fill="${c}"/>`;
    case 'wild': return `<circle cx="13" cy="26" r="9" fill="${c}"/><circle cx="51" cy="26" r="9" fill="${c}"/><circle cx="16" cy="16" r="7" fill="${c}"/><circle cx="48" cy="16" r="7" fill="${c}"/><circle cx="11" cy="36" r="6" fill="${c}"/><circle cx="53" cy="36" r="6" fill="${c}"/>`;
    default: return '';
  }
}
function hairFront(a, c){
  switch (a.hair) {
    case 'short': return `<path d="M16 30 Q15 13 32 13 Q49 13 48 30 Q44 21 33 21 Q22 20 16 30 Z" fill="${c}"/>`;
    case 'buzz': return `<path d="M17 28 Q17 15 32 15 Q47 15 47 28 Q40 20 32 20 Q24 20 17 28 Z" fill="${c}"/>`;
    case 'spiky': return `<path d="M15 30 L17 17 L22 21 L25 11 L30 18 L34 9 L38 18 L43 12 L44 21 L49 17 L49 30 Q42 21 32 21 Q22 21 15 30 Z" fill="${c}"/>`;
    case 'curly': return `<g fill="${c}">${[[18,22],[24,16],[32,14],[40,16],[46,22],[16,29],[48,29]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="6"/>`).join('')}</g>`;
    case 'bob': return `<path d="M14 38 Q12 13 32 13 Q52 13 50 38 L45 38 Q46 24 32 22 Q19 23 19 38 Z" fill="${c}"/>`;
    case 'long': case 'ponytail': case 'braids': case 'buns': return `<path d="M16 31 Q15 13 32 13 Q49 13 48 31 Q45 22 36 20 Q32 25 24 23 Q19 25 16 31 Z" fill="${c}"/>`;
    case 'afro': return `<path d="M16 30 Q17 17 32 17 Q47 17 48 30 Q41 23 32 23 Q23 23 16 30 Z" fill="${c}"/>`;
    case 'mohawk': return `<path d="M27 25 L28 6 L32 3 L36 6 L37 25 Q32 22 27 25 Z" fill="${c}"/>`;
    case 'wild': return `<path d="M20 22 Q26 18 30 22 Q34 17 38 22 Q42 18 46 22 L46 25 Q32 20 18 25 Z" fill="${c}"/>`;
    case 'tuft': return `<path d="M28 18 Q30 8 33 13 Q35 6 37 15 Q34 15 32 19 Z" fill="${c}"/>`;
    default: return '';
  }
}
function eyes(a){
  const ink = '#1d2026';
  switch (a.eyes) {
    case 'glasses': return `<circle cx="25" cy="34" r="2.2" fill="${ink}"/><circle cx="39" cy="34" r="2.2" fill="${ink}"/><g fill="none" stroke="#2a2f38" stroke-width="2"><circle cx="25" cy="34" r="5.5"/><circle cx="39" cy="34" r="5.5"/><path d="M30.5 34h3"/></g>`;
    case 'monocle': return `<circle cx="25" cy="34" r="2.2" fill="${ink}"/><circle cx="39" cy="34" r="2.2" fill="${ink}"/><circle cx="39" cy="34" r="5.5" fill="none" stroke="#c9a227" stroke-width="2"/><path d="M44 37 Q47 44 44 50" fill="none" stroke="#c9a227" stroke-width="1.2"/>`;
    case 'goggles': return `<path d="M15 33h34" stroke="#3a3f47" stroke-width="3"/><g stroke="#3a3f47" stroke-width="2.5"><circle cx="25" cy="34" r="6.5" fill="#9fe3f0"/><circle cx="39" cy="34" r="6.5" fill="#9fe3f0"/></g><circle cx="25" cy="34" r="2.4" fill="${ink}"/><circle cx="39" cy="34" r="2.4" fill="${ink}"/><circle cx="23" cy="32" r="1.4" fill="#fff"/><circle cx="37" cy="32" r="1.4" fill="#fff"/>`;
    case 'big': return `<ellipse cx="25" cy="33" rx="5" ry="6" fill="#111"/><ellipse cx="39" cy="33" rx="5" ry="6" fill="#111"/><circle cx="23.5" cy="31" r="1.8" fill="#fff"/><circle cx="37.5" cy="31" r="1.8" fill="#fff"/>`;
    case 'led': return `<rect x="20" y="31" width="9" height="5" rx="2" fill="#3cf0d8"/><rect x="35" y="31" width="9" height="5" rx="2" fill="#3cf0d8"/>`;
    case 'cyclops': return `<circle cx="32" cy="32" r="8" fill="#fff"/><circle cx="33" cy="33" r="4" fill="#2a6a3a"/><circle cx="33" cy="33" r="2" fill="#111"/><circle cx="31" cy="31" r="1.2" fill="#fff"/>`;
    default: return `<circle cx="25" cy="34" r="2.4" fill="${ink}"/><circle cx="39" cy="34" r="2.4" fill="${ink}"/><circle cx="24.2" cy="33.2" r=".8" fill="#fff"/><circle cx="38.2" cy="33.2" r=".8" fill="#fff"/>`;
  }
}
function mouth(a){
  switch (a.mouth) {
    case 'grin': return `<path d="M25 42 Q32 50 39 42 Z" fill="#7a2a2a"/><path d="M27 43.5 Q32 47 37 43.5" fill="#f4f4f4"/>`;
    case 'teeth': return `<path d="M23 41 Q32 51 41 41 Z" fill="#7a2a2a"/><path d="M24 41.5h16 l-1.5 2.5h-13z" fill="#fff"/>`;
    case 'flat': return `<rect x="25" y="42" width="14" height="3" rx="1.5" fill="#3a3f47"/><path d="M28 42v3M31 42v3M34 42v3M37 42v3" stroke="#b9c2cc" stroke-width=".8"/>`;
    default: return `<path d="M26 42 Q32 47 38 42" fill="none" stroke="#5a2424" stroke-width="2" stroke-linecap="round"/>`;
  }
}
function extras(a, back){
  const x = a.extra, out = [];
  if (back) { if (x.includes('antennae')) out.push(`<g stroke="#5fa84a" stroke-width="2"><path d="M24 20 L18 7"/><path d="M40 20 L46 7"/></g><circle cx="18" cy="7" r="3" fill="#f0e25a"/><circle cx="46" cy="7" r="3" fill="#f0e25a"/>`);
    if (x.includes('bolt')) out.push(`<path d="M32 18V8" stroke="#8a939c" stroke-width="2"/><circle cx="32" cy="7" r="3" fill="#ff7b6c"/>`);
    if (x.includes('horns')) out.push(`<path d="M19 22 L16 12 L24 18 Z M45 22 L48 12 L40 18 Z" fill="#f0e8d8"/>`);
    return out.join(''); }
  if (x.includes('coat')) out.push(`<path d="M10 64 Q12 52 24 50 L32 60 L40 50 Q52 52 54 64 Z" fill="#f4f6f8"/><path d="M24 50 L32 60 L40 50 L36 49 L32 54 L28 49 Z" fill="#dfe5ea"/>`);
  if (x.includes('bowtie')) out.push(`<path d="M26 53 L32 56 L38 53 L38 60 L32 57 L26 60 Z" fill="#e8484a"/>`);
  if (x.includes('freckles')) out.push(`<g fill="#b06a48" opacity=".75"><circle cx="21" cy="39" r=".9"/><circle cx="23.5" cy="40.5" r=".9"/><circle cx="20" cy="41.5" r=".9"/><circle cx="43" cy="39" r=".9"/><circle cx="40.5" cy="40.5" r=".9"/><circle cx="44" cy="41.5" r=".9"/></g>`);
  if (x.includes('blush')) out.push(`<circle cx="20" cy="40" r="3" fill="#f28a8a" opacity=".45"/><circle cx="44" cy="40" r="3" fill="#f28a8a" opacity=".45"/>`);
  if (x.includes('brows')) out.push(`<path d="M19 28 L29 30 M45 28 L35 30" stroke="${HAIR[a.hc]}" stroke-width="3" stroke-linecap="round"/>`);
  if (x.includes('tache')) out.push(`<path d="M24 41 Q28 37 32 40 Q36 37 40 41 Q36 42 32 41 Q28 42 24 41 Z" fill="${HAIR[a.hc]}"/>`);
  if (x.includes('gogup')) out.push(`<path d="M15 23h34" stroke="#3a3f47" stroke-width="3"/><g stroke="#3a3f47" stroke-width="2"><circle cx="25" cy="22" r="5" fill="#9fe3f0"/><circle cx="39" cy="22" r="5" fill="#9fe3f0"/></g>`);
  if (x.includes('headset')) out.push(`<path d="M15 32 Q15 12 32 12 Q49 12 49 32" fill="none" stroke="#2f3540" stroke-width="2.5"/><rect x="11" y="29" width="6" height="10" rx="3" fill="#2f3540"/><rect x="47" y="29" width="6" height="10" rx="3" fill="#2f3540"/><path d="M14 38 Q16 46 25 45" fill="none" stroke="#2f3540" stroke-width="1.8"/><circle cx="25.5" cy="45" r="1.8" fill="#ff7b6c"/>`);
  if (x.includes('helmet')) out.push(`<circle cx="32" cy="33" r="25" fill="rgba(190,230,255,.18)" stroke="#e9eef3" stroke-width="3"/><path d="M14 25 Q20 14 30 12" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" opacity=".8"/>`);
  if (x.includes('uniform')) out.push(`<path d="M10 64 Q12 52 24 50 L32 60 L40 50 Q52 52 54 64 Z" fill="#1f3b63"/><path d="M24 50 L32 60 L40 50 L36 49 L32 54 L28 49 Z" fill="#f4f6f8"/><circle cx="32" cy="62" r="1.3" fill="#d8b24a"/>`);
  if (x.includes('tie')) out.push(`<path d="M10 64 Q12 52 24 50 L32 58 L40 50 Q52 52 54 64 Z" fill="#6b5b4b"/><path d="M28 50 L32 56 L36 50 Z" fill="#f4f6f8"/><path d="M30.5 54 L33.5 54 L34.5 64 L29.5 64 Z" fill="#a8322d"/>`);
  if (x.includes('scarf')) out.push(`<path d="M18 50 Q32 58 46 50 L47 55 Q32 63 17 55 Z" fill="#c0392b"/><path d="M38 56 L44 64 L38 64 Z" fill="#a8322d"/>`);
  if (x.includes('cap')) out.push(`<path d="M13 21 Q32 6 51 21 L49 25 L15 25 Z" fill="#f4f6f8"/><rect x="14" y="23" width="36" height="5" rx="2" fill="#1f2a3a"/><path d="M16 27 Q32 33 48 27 L46 30 Q32 35 18 30 Z" fill="#111820"/><circle cx="32" cy="18" r="3" fill="#d8b24a"/>`);
  if (x.includes('fedora')) out.push(`<path d="M8 25 Q32 31 56 25 Q52 29 32 31 Q12 29 8 25 Z" fill="#4a3b2e"/><path d="M17 25 Q16 8 32 9 Q48 8 47 25 Q32 28 17 25 Z" fill="#5d4a39"/><path d="M17 21 Q32 25 47 21 L47 25 Q32 28 17 25 Z" fill="#2a211a"/><path d="M27 10 Q32 14 37 10" stroke="#4a3b2e" stroke-width="2" fill="none"/>`);
  if (x.includes('beret')) out.push(`<path d="M12 22 Q14 8 34 8 Q54 9 52 20 Q44 25 30 24 Q18 24 12 22 Z" fill="#2b3a55"/><circle cx="33" cy="7" r="2.2" fill="#2b3a55"/>`);
  return out.join('');
}
/* The SVG for one avatar, drawn in a 64 x 64 box. */
SC.avatarSvg = id => {
  const a = SC.AVATARS[id]; if (!a) return '';
  const skin = SKIN[a.skin], hc = HAIR[a.hc], robot = a.skin === 'robot';
  const head = robot ? `<rect x="15" y="17" width="34" height="34" rx="7" fill="${skin}"/><rect x="11" y="28" width="5" height="12" rx="2" fill="${darker(skin, .75)}"/><rect x="48" y="28" width="5" height="12" rx="2" fill="${darker(skin, .75)}"/><circle cx="19" cy="21" r="1.3" fill="${darker(skin, .6)}"/><circle cx="45" cy="21" r="1.3" fill="${darker(skin, .6)}"/>`
    : `<rect x="27" y="44" width="10" height="10" fill="${darker(skin, .9)}"/><circle cx="16" cy="35" r="4" fill="${darker(skin, .93)}"/><circle cx="48" cy="35" r="4" fill="${darker(skin, .93)}"/><ellipse cx="32" cy="33" rx="16" ry="17" fill="${skin}"/>`;
  return `<svg class="avsvg" viewBox="0 0 64 64" aria-hidden="true">${extras(a, true)}${hairBack(a, hc)}${head}${hairFront(a, hc)}${eyes(a)}${mouth(a)}${extras(a, false)}</svg>`;
};
})();

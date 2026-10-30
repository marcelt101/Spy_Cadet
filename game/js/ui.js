/* Screens and popups that are not the workstation: home, profiles, settings, Records Room, the teacher page,
   toasts, and the folders (briefing, outcome, history card). Modal and toast helpers follow Crater Crew. */
(function () {
const SC = window.SC;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, m => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'}[m]));
const UI = SC.UI = {$, esc};

UI.avatar = (p, cls = '') => p && p.avatar != null && SC.AVATARS[p.avatar]
  ? `<span class="av pic ${cls}" style="background:${SC.colorHex(p.color)}" title="${esc(p.name || SC.AVATARS[p.avatar].name)}">${SC.avatarSvg(p.avatar)}</span>`
  : `<span class="av ${cls}" style="background:${SC.colorHex(p && p.color)}">${esc(((p && p.name) || '?').slice(0, 1).toUpperCase())}</span>`;
UI.mentorAvatar = (cls = '') => `<span class="av pic ${cls}" style="background:#d9c597" title="${esc(SC.MENTOR.name)}">${SC.avatarSvg(SC.MENTOR.avatar)}</span>`;
UI.starsHtml = n => [0, 1, 2].map(i => `<span class="${i < n ? 'on' : ''}">★</span>`).join('');
UI.show = name => { ['scrHome', 'scrMap', 'scrLobby', 'scrDesk'].forEach(s => $(s).hidden = s !== name); scrollTo(0, 0); };

/* ---------- toasts ---------- */
UI.toast = (icon, title, sub, ms = 4200) => {
  const t = document.createElement('div'); t.className = 'toast'; t.innerHTML = `<span class="ti">${icon}</span><span><b>${esc(title)}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</span>`;
  $('toasts').append(t); while ($('toasts').children.length > 3) $('toasts').firstChild.remove();
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 350); }, ms);
};
UI.notify = notices => (notices || []).forEach(n => {
  if (n.k === 'patch') { const pt = SC.PATCHES.find(x => x.id === n.id); UI.toast(pt.icon, `Patch earned: ${pt.name}`, pt.what, 5200); SC.sfx.bell(); }
  if (n.k === 'rank') { UI.toast('🎖', `Promoted to ${SC.RANKS[n.rank].name}!`, 'Your ID badge has been updated.', 6000); SC.sfx.win(); }
});

/* ---------- modal ---------- */
let modalClose = null;
UI.openModal = (html, narrow, onClose) => { $('sheet').className = 'sheet' + (narrow ? ' narrow' : ''); $('sheet').innerHTML = html; $('modal').hidden = false; modalClose = onClose || null; };
UI.closeModal = () => { if ($('modal').hidden) return; $('modal').hidden = true; $('sheet').innerHTML = ''; const f = modalClose; modalClose = null; if (f) f(); };
UI.modalOpen = () => !$('modal').hidden;
$('modal').addEventListener('click', e => { if (e.target.id === 'modal' || e.target.closest('[data-close]')) UI.closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && UI.modalOpen()) UI.closeModal(); });
const head = title => `<div class="sh"><h2>${esc(title)}</h2><button class="xbtn" data-close aria-label="Close">×</button></div>`;

/* ---------- folders ---------- */
UI.folder = (tab, html) => { $('folderBody').dataset.tab = tab; $('folderBody').innerHTML = html; $('folder').hidden = false; $('folderBody').style.animation = 'none'; void $('folderBody').offsetWidth; $('folderBody').style.animation = ''; };
UI.closeFolder = () => { $('folder').hidden = true; $('folderBody').innerHTML = ''; SC.speech.stop(); };
UI.folderOpen = () => !$('folder').hidden;
/* Print text a letter at a time, like a teletype. */
UI.typeOut = (el, text, done, speed = 22) => {
  let i = 0; el.textContent = ''; const step = () => { if (!el.isConnected) return;
    el.textContent = text.slice(0, ++i); if (i % 3 === 0) SC.sfx.key();
    if (i < text.length) setTimeout(step, text[i - 1] === '\n' ? 250 : speed); else if (done) done(); };
  step();
};

/* ---------- home ---------- */
UI.renderHome = () => {
  const list = SC.Store.profiles(), cur = SC.Store.current();
  $('profiles').innerHTML = list.map(p => { const ri = SC.rankInfo(p);
    return `<div class="badge" role="button" tabindex="0" data-id="${p.id}" aria-pressed="${!!cur && cur.id === p.id}">${UI.avatar(p, 'lg')}<span style="min-width:0;flex:1"><b>${esc(p.name)}</b>
      <small>${esc(ri.name)} · ${esc(SC.LEVELS[p.level].label)}</small><div class="xp"><span style="width:${Math.round(ri.frac * 100)}%"></span></div></span>
      <button class="edit" data-edit="${p.id}" aria-label="Edit ${esc(p.name)}">✎</button></div>`; }).join('')
    + `<button class="badge new" id="newProfile">${list.length ? '+ New cadet' : '+ Make your ID badge to start'}</button>`;
  $('modes').classList.toggle('locked', !cur);
  const net = SC.netAvailable(); $('hostBtn').disabled = !cur || !net; $('joinBtn').disabled = !cur || !net;
};
$('profiles').addEventListener('click', e => {
  const ed = e.target.closest('[data-edit]'); if (ed) { UI.profileModal(SC.Store.profiles().find(p => p.id === ed.dataset.edit)); return; }
  if (e.target.closest('#newProfile')) return UI.profileModal(null);
  const b = e.target.closest('.badge[data-id]'); if (!b) return;
  SC.Store.select(b.dataset.id); SC.sfx.stamp(); UI.renderHome();
});
$('profiles').addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('.badge[data-id]')) { e.preventDefault(); e.target.click(); } });

/* ---------- profile editor ---------- */
UI.profileModal = existing => {
  const p = existing || {name:'', color:SC.COLORS[SC.Store.profiles().length % SC.COLORS.length].id, avatar:Math.floor(Math.random() * SC.PICK_AVATARS), level:'codebreaker'};
  let color = p.color, avatar = p.avatar, level = p.level;
  UI.openModal(`${head(existing ? 'Edit ID badge' : 'New cadet')}<div class="sb">
    <label class="field"><span>Codename (no real names needed)</span><input class="input" id="pfName" maxlength="16" value="${esc(p.name)}" placeholder="e.g. Agent Fox" autocomplete="off"></label>
    <h3>Your face</h3><div class="avgrid" id="pfAv">${[...Array(SC.PICK_AVATARS).keys()].map(i => `<button aria-pressed="${i === avatar}" data-av="${i}" aria-label="${esc(SC.AVATARS[i].name)}">${UI.avatar({avatar:i, color})}</button>`).join('')}</div>
    <h3>Your color</h3><div class="swatches" id="pfCol">${SC.COLORS.map(c => `<button style="background:${c.hex}" aria-pressed="${c.id === color}" data-col="${c.id}" aria-label="${c.id}"></button>`).join('')}</div>
    <h3>Your level</h3><div class="levels" id="pfLvl">${SC.LEVEL_ORDER.map(k => `<button aria-pressed="${k === level}" data-lvl="${k}"><b>${SC.LEVELS[k].label}</b><small>Ages ${SC.LEVELS[k].ages}</small><small>${SC.LEVELS[k].blurb}</small></button>`).join('')}</div>
    <div class="row" style="justify-content:space-between;margin-top:20px">${existing ? '<button class="btn red" id="pfDel">Delete</button>' : '<span></span>'}<button class="btn gold" id="pfSave">${existing ? 'Save' : 'Report for duty'}</button></div></div>`, true);
  const redrawAv = () => $('pfAv').querySelectorAll('[data-av]').forEach(b => { b.innerHTML = UI.avatar({avatar:+b.dataset.av, color}); b.setAttribute('aria-pressed', +b.dataset.av === avatar); });
  $('pfAv').onclick = e => { const b = e.target.closest('[data-av]'); if (b) { avatar = +b.dataset.av; redrawAv(); SC.sfx.click(); } };
  $('pfCol').onclick = e => { const b = e.target.closest('[data-col]'); if (b) { color = b.dataset.col; $('pfCol').querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); redrawAv(); SC.sfx.click(); } };
  $('pfLvl').onclick = e => { const b = e.target.closest('[data-lvl]'); if (b) { level = b.dataset.lvl; $('pfLvl').querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); SC.sfx.click(); } };
  $('pfSave').onclick = () => {
    const name = $('pfName').value.trim(); if (!name) { $('pfName').focus(); return; }
    if (existing) Object.assign(existing, {name:name.slice(0, 16), color, avatar, level}), SC.Store.save(); else SC.Store.create({name, color, avatar, level});
    SC.sfx.stamp(); UI.closeModal(); UI.renderHome(); if (SC.Map && !$('scrMap').hidden) SC.Map.render();
  };
  if ($('pfDel')) $('pfDel').onclick = () => { if (confirm(`Delete ${existing.name}? Their progress on this device is lost.`)) { SC.Store.remove(existing.id); UI.closeModal(); UI.renderHome(); } };
  setTimeout(() => $('pfName').focus(), 60);
};

/* ---------- settings ---------- */
const tog = (id, on, label, sub) => `<label class="sset"><span><b>${label}</b>${sub ? `<small>${sub}</small>` : ''}</span><input type="checkbox" class="swi" id="${id}" ${on ? 'checked' : ''}></label>`;
UI.settings = () => {
  const s = SC.Store.settings;
  UI.openModal(`${head('Settings')}<div class="sb">
    <h3>Sound</h3>${tog('stSound', s.sound, 'Sound effects', 'Typewriter keys, stamps and the teletype.')}${tog('stMusic', s.music !== false, 'Music', 'A quiet music bed and a clock tick when time is short.')}
    <label class="sset"><span><b>Music volume</b></span><input type="range" id="stVol" min="0" max="100" step="5" value="${s.musicVol ?? 35}" aria-label="Music volume"></label>
    ${tog('stVoice', s.voice !== false, 'Read aloud', 'The mentor reads briefings aloud when you tap 🔊.')}
    <h3>Teachers</h3>${tog('stAll', !!s.allMissions, 'Open all missions', 'Skip ahead without finishing earlier missions, on this device.')}
    <h3>Saves</h3><div class="sset"><span><b>Backup code</b><small>Copy it somewhere safe, or paste one to bring profiles to this device.</small></span><button class="btn" id="stExport">Show code</button></div>
    <div class="sset"><span><b>Restore</b></span><button class="btn" id="stImport">Paste code</button></div>
    <p class="muted" style="font-size:13px;margin-top:18px">Spy Cadet · campaign 1 test build. Fonts: Atkinson Hyperlegible, Special Elite, Black Ops One (SIL OFL). Networking and avatars from Crater Crew.</p></div>`, true);
  $('stSound').onchange = e => { s.sound = e.target.checked; SC.Store.save(); };
  $('stMusic').onchange = e => { s.music = e.target.checked; SC.Store.save(); SC.music.refresh(); };
  $('stVol').oninput = e => { s.musicVol = +e.target.value; SC.Store.save(); SC.music.refresh(); };
  $('stVoice').onchange = e => { s.voice = e.target.checked; SC.Store.save(); };
  $('stAll').onchange = e => { s.allMissions = e.target.checked; SC.Store.save(); if (SC.Map) SC.Map.render(); };
  $('stExport').onclick = () => { const code = SC.Store.exportCode(); try { navigator.clipboard.writeText(code); } catch (e) {} prompt('Your backup code (copied):', code); };
  $('stImport').onclick = () => { const c = prompt('Paste a backup code:'); if (!c) return; try { const n = SC.Store.importCode(c); UI.toast('✅', `Restored ${n} profile${n === 1 ? '' : 's'}`); UI.renderHome(); } catch (e) { alert('That code did not work.'); } };
};

/* ---------- records room ---------- */
UI.records = () => {
  const p = SC.Store.current();
  const people = Object.entries(SC.PEOPLE).map(([id, pr]) => { const has = p && p.people[id];
    return has ? `<button class="rcard" data-person="${id}"><span class="rp">🕯</span><b>${esc(pr.name)}</b><small>${esc(pr.role)}</small></button>`
      : `<div class="rcard locked"><span class="rp">?</span><b>Locked</b><small>Finish more missions to add this story.</small></div>`; }).join('');
  const patches = SC.PATCHES.map(pt => `<div class="patch ${p && p.patches[pt.id] ? 'on' : ''}"><span class="pi">${pt.icon}</span><b>${esc(pt.name)}</b><small>${esc(pt.what)}</small></div>`).join('');
  UI.openModal(`${head('Records Room')}<div class="sb">
    <p class="muted">The people who really did this work. Many of them kept it secret for decades. The war took tens of millions of lives, on every side; this room remembers them.</p>
    <h3>People</h3><div class="records" id="recPeople">${people}</div>
    <h3>Patches ${p ? `<span class="pill">${Object.keys(p.patches).length} / ${SC.PATCHES.length}</span>` : ''}</h3><div class="patches">${patches}</div></div>`);
  $('recPeople').onclick = e => { const b = e.target.closest('[data-person]'); if (!b) return; UI.person(b.dataset.person); };
};
UI.person = id => {
  const pr = SC.PEOPLE[id], p = SC.Store.current();
  if (p && !p.read[id]) { p.read[id] = 1; UI.notify(SC.reward(p, 'cards', 1, 5)); }
  UI.openModal(`${head(pr.name)}<div class="sb"><div class="hcard"><div class="photo">${photo(id)}</div><div>
    <p class="muted" style="margin-top:0">${esc(pr.role)}${pr.years ? ` · ${esc(pr.years)}` : ''}</p>${pr.lines.map(l => `<p>${esc(l)}</p>`).join('')}</div></div></div>`, true, () => UI.records());
};
/* Photos of real people go in img/people/<id>.jpg (see ASSETS.md). Until a file is there, a labeled frame shows what goes there. */
const photo = id => `<span>Photo to come:<br><b>${esc((SC.PEOPLE[id] || {}).name || id)}</b></span><img src="img/people/${esc(id)}.jpg" alt="${esc((SC.PEOPLE[id] || {}).name || '')}" onerror="this.remove()">`;

/* ---------- for teachers ---------- */
UI.teachers = () => {
  UI.openModal(`${head('For teachers')}<div class="sb teach">
    <p><b>Spy Cadet</b> lets a class decode real World War II style messages together. Campaign 1, <i>The Midway Code</i>, follows the US Navy codebreakers at Pearl Harbor in 1942. Ages 8 to 14; one mission fits about 15 to 25 minutes.</p>
    <h3>How a team game works</h3><ol><li>Open the game on your computer and tap <b>Host a team game</b>. Put the room code on the projector.</li>
      <li>Students open the game on their Chromebooks, make an ID badge (codenames only) and tap <b>Join</b>.</li>
      <li>Pick a mission and the clock, and start. Every student gets their own intercepted messages. A word one student works out appears in everyone's codebook.</li>
      <li>At each big decision the class votes. A wrong answer is explained, and the class votes again: a good moment to stop and discuss.</li></ol>
    <h3>What students practice</h3><ul><li>Digit-by-digit subtraction without borrowing (mod 10), and the "divides by 3" digit-sum check.</li>
      <li>Reading clues in context and ruling out wrong answers.</li><li>The history of the Pacific war in 1942: Coral Sea, the AF trap and Midway, and the real people involved.</li>
      <li>The big idea: codes are usually broken because of habits and teamwork, not just machines.</li></ul>
    <h3>Privacy</h3><p>No accounts and no personal data. Progress stays on each device. Devices find each other through the free PeerJS service and then talk directly; there is no chat, only game moves.</p>
    <h3>Honest history</h3><p>Every mission ends with a "What really happened" card that says what the game simplified. Losses are mentioned honestly, without graphic detail and never as a score.</p></div>`);
};

/* ---------- briefing ---------- */
UI.briefing = (mid, onStart) => {
  const {c, m, i} = SC.Engine.find(mid), lvl = (SC.Store.current() || {}).level || 'codebreaker', lim = SC.Engine.limitFor(m, lvl);
  UI.folder('MISSION ' + (i + 1), `<div class="paper"><div class="stamp corner tilt slam">Top Secret</div>
    <h2>${esc(m.title)}</h2><div class="meta"><span>📅 ${esc(m.date)}</span><span>📍 ${esc(m.place)}</span><span>${lim ? `⏱ ${Math.round(lim / 60)} min clock` : '⏱ No clock'}</span></div>
    <div class="brief"><div class="minimap">${SC.Map.mini(m.pin)}</div><div style="flex:1">
      <div class="speech">${UI.mentorAvatar('lg')}<div class="bubble">${m.briefing.map(t => `<p>${esc(t)}</p>`).join('')}</div></div></div></div>
    <div class="goal">${esc(m.goal)}</div>
    <div class="acts"><button class="btn" id="brSay">🔊 Read aloud</button><button class="btn" id="brBack">Not yet</button><button class="btn gold" id="brGo">Start mission ▶</button></div></div>`);
  SC.sfx.stamp();
  $('brSay').onclick = () => SC.speech.say(m.briefing.join(' ') + ' Your goal: ' + m.goal);
  $('brBack').onclick = () => UI.closeFolder();
  $('brGo').onclick = () => { UI.closeFolder(); onStart(); };
};

/* ---------- outcome and history card ---------- */
UI.outcome = ({mid, result, stars, gains, team, onDone}) => {
  const {m} = SC.Engine.find(mid), lines = (m.outcome[result] || m.outcome.win);
  UI.folder('RESULT', `<div class="paper"><div class="stamp corner tilt ${result === 'win' ? 'green' : ''}" id="ocStamp" hidden>${result === 'win' ? 'Mission complete' : 'Completed late'}</div>
    <h2>${esc(m.title)}</h2><div class="meta"><span>📅 ${esc(m.date)}</span>${team ? '<span>👥 Team game</span>' : ''}</div>
    <div class="teletype" id="ocTape"></div>
    <div class="result-stars" id="ocStars">${UI.starsHtml(0)}</div>
    <div class="gains" id="ocGains" hidden>${gains.map(g => `<span>${esc(g)}</span>`).join('')}</div>
    <div class="acts"><button class="btn gold" id="ocNext" disabled>What really happened →</button></div></div>`);
  SC.sfx.teletype(10);
  UI.typeOut($('ocTape'), lines.join('\n'), () => {
    $('ocStamp').hidden = false; $('ocStamp').classList.add('slam'); SC.sfx.stamp();
    [...$('ocStars').children].forEach((s, k) => { if (k < stars) setTimeout(() => { s.classList.add('on'); SC.sfx.ok(); }, 500 + k * 380); });
    setTimeout(() => { $('ocGains').hidden = false; $('ocNext').disabled = false; if (result === 'win') SC.sfx.win(); }, 600 + stars * 380);
  });
  $('ocNext').onclick = () => UI.history(mid, onDone);
};
UI.history = (mid, onDone) => {
  const {m} = SC.Engine.find(mid), h = m.history, pr = SC.PEOPLE[h.person];
  UI.folder('WHAT REALLY HAPPENED', `<div class="paper"><h2>${esc(h.title)}</h2><div class="meta"><span>📅 ${esc(m.date)}</span></div>
    <div class="hcard"><div class="photo">${photo(h.person)}</div><div><ul>${h.lines.map(l => `<li>${esc(l)}</li>`).join('')}</ul><p class="simple">${esc(h.simplified)}</p></div></div>
    <div class="person"><b>${esc(pr.name)}</b><small>${esc(pr.role)}${pr.years ? ` · ${esc(pr.years)}` : ''} · added to your Records Room</small>${pr.lines.map(l => `<p>${esc(l)}</p>`).join('')}</div>
    <div class="acts"><button class="btn" id="hcSay">🔊 Read aloud</button><button class="btn gold" id="hcDone">Continue</button></div></div>`);
  $('hcSay').onclick = () => SC.speech.say(h.lines.join(' ') + ' ' + pr.name + '. ' + pr.lines.join(' '));
  $('hcDone').onclick = () => { UI.closeFolder(); onDone && onDone(); };
};

$('setBtn').onclick = UI.settings;
$('recordsBtn').onclick = UI.records;
$('teachBtn').onclick = UI.teachers;
})();

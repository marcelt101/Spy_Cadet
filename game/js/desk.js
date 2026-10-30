/* The workstation. The intercept strip on top, the subtraction bench in the middle, the codebook and the board on
   the side, the news teletype and the clock on top, and the mentor at the bottom saying what to do next.
   Progress on a message is kept on this device; only finished results (a word worked out, a message filed,
   a vote) go to the host. */
(function () {
const SC = window.SC, UI = SC.UI, {$, esc} = UI, C = SC.Code, E = SC.Engine;
const G = () => SC.Game;
const D = SC.Desk = {prog:{}, hit:null, result:null, why:null, waiting:false, tab:'book', hintN:0, voteHidden:{}, machineRun:false, offered:{}};
const me = () => SC.Store.current();
const lvl = () => SC.LEVELS[(me() || {}).level || 'codebreaker'];
const prog = iid => D.prog[iid] || (D.prog[iid] = {done:G().B.byId[iid].groups.map(() => false), typed:'', gi:0, manual:0, tries:0, flash:null});
const wordOf = (st, B, w) => E.known(st, B, w) ? w : null;
const pidName = pid => { const p = G().players().find(x => x.pid === pid); return p ? p.name : 'A teammate'; };

D.reset = () => Object.assign(D, {prog:{}, hit:null, result:null, why:null, waiting:false, hintN:0, voteHidden:{}, machineRun:false, offered:{}});
D.say = (text, sub) => { $('mentorSay').innerHTML = esc(text) + (sub ? `<small>${esc(sub)}</small>` : ''); $('mentor').classList.remove('talk'); void $('mentor').offsetWidth; $('mentor').classList.add('talk'); D.said = text; };

/* ---------- the whole desk ---------- */
D.enter = () => {
  const {m, i} = E.find(G().st.mid);
  $('deskTitle').textContent = `Mission ${i + 1}: ${m.title}`;
  $('mentorAv').innerHTML = UI.mentorAvatar();
  $('tape').innerHTML = '<span class="line new">STATION HYPO TELETYPE READY<span class="cur"></span></span>';
  D.render();
};
D.render = () => { const g = G(); if (!g.st) return; renderBench(); renderBook(); renderBoard(); renderClock(); renderCrew(); renderStep(); };
const renderStep = () => { const ph = E.phase(G().st), {m} = E.find(G().st.mid);
  $('deskStep').textContent = ph ? `Step ${G().st.phase + 1} of ${m.phases.length}: ${ph.k === 'vote' ? 'decision' : 'decode the messages'}` : 'Mission complete'; };

function renderBench(){
  const g = G(), st = g.st, B = g.B, ph = E.phase(st), el = $('bench');
  if (D.result) { el.innerHTML = resultCard(); return bindResult(); }
  if (!ph) { el.innerHTML = `<div class="vote done-msg"><div class="stamp green tilt">Complete</div></div>`; return; }
  if (ph.k === 'vote') { el.innerHTML = voteCard(ph); return bindVote(ph); }
  const iid = st.assign[g.myPid];
  if (!iid) { el.innerHTML = waitCard(); D.say(D.waiting ? SC.SAY.wait : SC.SAY.allFiled, D.waiting ? 'Read the board while your team finishes their messages.' : ''); return; }
  const x = B.byId[iid], pr = prog(iid), allDone = pr.done.every(Boolean), missing = E.missing(st, B, iid);
  let lower;
  if (!allDone) lower = workCard(x, pr);
  else if (missing.length) lower = deduceCard(x, missing[0]);
  else lower = fileCard(x);
  el.innerHTML = interceptCard(x, pr) + lower;
  bindBench(x, pr, allDone, missing);
}

/* ---------- the intercept ---------- */
function interceptCard(x, pr){
  const st = G().st, B = G().B;
  const groups = x.groups.map((g, k) => { const done = pr.done[k], w = done ? wordOf(st, B, g.word) : null, unk = done && !w;
    const rec = done && w && B.unknown.has(g.word);
    return `<div class="grp ${k === pr.gi && !pr.done.every(Boolean) ? 'cur' : ''} ${done ? 'done' : ''} ${unk ? 'unk' : ''} ${rec ? 'rec' : ''}" data-g="${k}">
      <span class="c">${g.cipher}</span><span class="w">${done ? (unk ? '?????' : esc(w)) : ''}</span></div>`; }).join('');
  const line = x.groups.map((g, k) => pr.done[k] ? (wordOf(st, B, g.word) ? esc(g.word) : '<span class="q">?????</span>') : '·····').join(' ');
  const plain = pr.done.every(Boolean) && x.key ? E.find(st.mid).m.messages[x.id].plain : '';
  return `<section class="intercept"><div class="ihead"><span><b>INTERCEPT</b> · ${esc(x.freq)} · ${esc(x.time)} hrs</span>${x.key ? '<span class="key">PRIORITY</span>' : '<span>routine</span>'}<span>Additive book line ${x.start + 1}</span></div>
    <div class="groups">${groups}</div><div class="decoded">${line}${plain ? `<span class="plain">${esc(plain)}</span>` : ''}</div></section>`;
}

/* ---------- strip one group ---------- */
function workCard(x, pr){
  const g = x.groups[pr.gi], col = pr.typed.length, showMath = lvl().showMath || pr.tries > 0 || (E.find(G().st.mid).m.tutorial && pr.manual < 3), chk = pr.flash;
  const row = (s, cls) => [...s].map((d, k) => `<span class="dg ${cls} ${k === col && cls !== 'ans' ? 'col' : ''}">${d}</span>`).join('');
  const ans = [0, 1, 2, 3, 4].map(k => `<span class="dg ans ${k === col ? 'at' : ''} ${chk && chk.bad && chk.at === k ? 'bad' : ''}" data-pos="${k}">${pr.typed[k] ?? ''}</span>`).join('');
  const c = +g.cipher[Math.min(col, 4)], k = +g.add[Math.min(col, 4)];
  const math = col < 5 && showMath ? `Digit ${col + 1}: ${c >= k ? C.digitMath(c, k) : `<span class="wrap">${C.digitMath(c, k)}</span>`}` : '';
  const machine = pr.manual >= lvl().manual && !D.offered[x.id];
  return `<section class="work"><div>
      <div class="sum"><span class="rl"><b>Message</b>group ${pr.gi + 1} of ${x.groups.length}</span>${row(g.cipher, '')}
        <span class="rl"><b>− Additive</b>from the book</span>${row(g.add, 'add')}<div class="minus"></div>
        <span class="rl"><b>= Code</b>group</span>${ans}</div>
      <div class="math" id="math">${math}</div>
    </div>
    <div><div class="pad" id="pad">${[1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map(n => `<button data-n="${n}">${n}</button>`).join('')}<button class="del wide" data-n="del">⌫ Undo</button></div>
      <div class="checker"><span class="bulb ${chk ? (chk.div3 ? 'ok' : 'bad') : ''}"></span><span><b>Divide-by-3 check</b><small>${chk ? (chk.div3 ? `Digits add up to ${chk.sum}: divides by 3.` : `Digits add up to ${chk.sum}: does not divide by 3!`) : 'Real code groups always divide by 3.'}</small></span></div>
    </div>${machine ? `<div class="machine" id="machine"><div class="ibm"><div class="lights"><i></i><i></i><i></i></div><div class="slot"></div><div class="card"></div></div>
      <span class="mtext"><b>The strip machine</b><small>HYPO's IBM punch-card machines did the sums for whole messages.</small></span>
      <button class="btn gold" id="runMachine">⚙ Run it on the rest</button></div>` : ''}</section>`;
}
function typeDigit(n){
  const g = G(), iid = g.st.assign[g.myPid]; if (!iid || D.machineRun) return;
  const pr = prog(iid); if (pr.done.every(Boolean)) return;
  if (n === 'del') { pr.typed = pr.typed.slice(0, -1); pr.flash = null; SC.sfx.click(); return renderBench(); }
  if (pr.typed.length >= 5) return;
  pr.typed += n; pr.flash = null; SC.sfx.key(); renderBench();
  const cell = $('bench').querySelector(`.dg.ans[data-pos="${pr.typed.length - 1}"]`); if (cell) cell.classList.add('pop');
  if (pr.typed.length === 5) setTimeout(() => checkGroup(iid), 260);
  else if (lvl().showMath) D.say(SC.SAY.goodDigit[Math.floor(Math.random() * 4)] + ' Next digit.');
  else if (pr.typed.length === 1) D.say(pr.tries ? 'Try again, one digit at a time.' : SC.SAY.stripMore);
}
function checkGroup(iid){
  const g = G(), pr = prog(iid), x = g.B.byId[iid], grp = x.groups[pr.gi], res = C.check(grp.cipher, grp.add, pr.typed), p = me();
  const sum = C.digitSum(pr.typed);
  if (res.ok) {
    const wraps = [...grp.cipher].filter((d, k) => +d < +grp.add[k]).length;
    pr.flash = {div3:true, sum}; pr.done[pr.gi] = true; pr.typed = ''; pr.tries = 0; pr.manual++;
    SC.sfx.ok(); UI.notify(SC.reward(p, 'hand', 1, SC.XP.hand)); if (wraps) UI.notify(SC.reward(p, 'wraps', wraps, 0));
    lookUp(grp);
    const next = pr.done.findIndex(d => !d);
    if (next >= 0) { pr.gi = next; D.say(pr.manual >= lvl().manual && !D.offered[iid] ? SC.SAY.machine : SC.SAY.stripMore); }
    renderBench();
    if (next < 0) afterStrip(iid);
    return;
  }
  pr.tries++; g.stats.slips++;
  pr.flash = {div3:res.div3 && C.div3(pr.typed), sum, bad:pr.tries >= 2, at:res.at};
  if (!C.div3(pr.typed)) { SC.sfx.bad(); UI.notify(SC.reward(p, 'caught', 1, 0)); D.say(SC.SAY.notDiv3, pr.tries >= 2 ? `Look at digit ${res.at + 1}.` : ''); }
  else { SC.sfx.bad(); D.say(SC.SAY.noMatch, pr.tries >= 2 ? `Look at digit ${res.at + 1}.` : ''); }
  renderBench();
  setTimeout(() => { if (G().st && G().st.assign[G().myPid] === iid) { pr.typed = ''; renderBench(); } }, 1100);
}
/* Look a stripped group up in the codebook: flip to it and light it up. */
function lookUp(grp){
  const g = G(); UI.notify(SC.reward(me(), 'looked', 1, SC.XP.look));
  D.hit = grp.code; if (D.tab !== 'book') showTab('book'); renderBook(true); SC.sfx.flip();
  if (!E.known(g.st, g.B, grp.word)) D.say(SC.SAY.unknown);
}
function afterStrip(iid){
  const g = G(), miss = E.missing(g.st, g.B, iid);
  D.say(miss.length ? SC.SAY.unknown : SC.SAY.read, miss.length ? 'It is marked ????? in red.' : '');
}
function runMachine(iid){
  const pr = prog(iid), x = G().B.byId[iid], left = pr.done.map((d, k) => d ? -1 : k).filter(k => k >= 0);
  D.offered[iid] = true; D.machineRun = true; $('machine').classList.add('run'); $('runMachine').disabled = true; D.say('The IBM machine is doing the sums…');
  let k = 0;
  const step = () => { if (!G().st || G().st.assign[G().myPid] !== iid) { D.machineRun = false; return; }
    if (k >= left.length) { D.machineRun = false; renderBench(); afterStrip(iid); return; }
    const gi = left[k++]; pr.done[gi] = true; pr.gi = gi; SC.sfx.teletype(4); UI.notify(SC.reward(me(), 'machine', 1, 0));
    D.hit = x.groups[gi].code; renderBook();
    const el = $('bench').querySelector(`.grp[data-g="${gi}"]`);
    if (el) { el.classList.add('done'); el.querySelector('.w').textContent = wordOf(G().st, G().B, x.groups[gi].word) || '?????'; if (!wordOf(G().st, G().B, x.groups[gi].word)) el.classList.add('unk'); }
    setTimeout(step, 420); };
  setTimeout(step, 500);
}

/* ---------- work out an unknown word ---------- */
function deduceCard(x, word){
  const g = G(), st = g.st, B = g.B, tg = E.find(st.mid).m.targets[word], code = g.B.book[word];
  const lines = B.intercepts.filter(y => y.words.includes(word) && (y.id === x.id || st.filed[y.id] || (D.prog[y.id] && D.prog[y.id].done.every(Boolean))))
    .map(y => `<li>${y.words.map(w => w === word ? `<span class="q">${code}</span>` : esc(w)).join(' ')}</li>`).join('');
  const opts = SC.shuffle(SC.rng(SC.hashSeed(word + st.seed)), tg.opts);
  const why = D.why && D.why.word === word ? D.why : null, hide = D.voteHidden['w:' + word];
  return `<section class="deduce"><h3>🔎 Unknown group ${code}</h3><p style="margin:0">This group is not in our codebook. Where it shows up:</p>
    <ul class="seen">${lines}</ul><div class="clue">💡 ${esc(tg.clue)}</div><p style="margin:0 0 10px;font-weight:700">What does ${code} mean?</p>
    <div class="opts">${opts.map(o => `<button class="opt ${why && why.guess === o ? 'no' : ''}" data-guess="${esc(o)}" ${hide === o ? 'disabled style="opacity:.35"' : ''}>${esc(o)}</button>`).join('')}</div>
    ${why ? `<div class="why">${esc(why.text)}</div>` : ''}</section>`;
}

/* ---------- file the message ---------- */
function fileCard(x){
  return `<div class="actionrow"><button class="big gold" id="fileBtn"><span class="ic">📌</span><span><b>File it on the board</b><small>${x.key ? 'A priority message: the commander needs this.' : 'Everyday traffic helps us learn the enemy\'s habits.'}</small></span></button></div>`;
}
function waitCard(){
  return `<section class="vote"><h3>Station HYPO</h3><h2>${D.waiting ? 'Your team is finishing the last messages' : 'All messages for this step are on the board'}</h2>
    <p>Have a look at the board on the right. The next step starts when the priority messages are filed.</p>
    <div class="vfoot"><button class="btn" id="tryTake">Look for another message</button></div></section>`;
}

/* ---------- the commander's decision ---------- */
function voteCard(ph){
  const g = G(), st = g.st, team = g.mode !== 'solo', mine = st.votes[g.myPid], players = g.players().filter(p => p.connected !== false);
  const opts = ph.opts.map((o, k) => { const who = players.filter(p => st.votes[p.pid] === k), hidden = D.voteHidden[ph.id + ':' + st.round] === k;
    return `<button class="vopt ${mine === k ? 'mine' : ''}" data-opt="${k}" ${hidden ? 'disabled style="opacity:.35"' : ''}><span class="letter">${'ABC'[k]}</span><span>${esc(o.t)}</span>
      ${team && who.length ? `<span class="who">${who.slice(0, 8).map(p => UI.avatar(p)).join('')}</span><span class="cnt">${who.length}</span>` : ''}</button>`; }).join('');
  const voted = Object.keys(st.votes).length;
  return `<section class="vote"><div class="stamp tilt">Decision</div><h3>${st.round ? `Try again: round ${st.round + 1}` : 'The commander asks'}</h3><h2>${esc(ph.q)}</h2>
    <div class="vopts">${opts}</div>
    <div class="vfoot">${team ? `<span>${voted} of ${players.length} voted. ${g.mode === 'host' ? 'The vote closes when everyone has voted.' : 'The host closes the vote.'}</span>` : '<span>Pick the best answer.</span>'}
      ${g.mode === 'host' ? `<button class="btn gold" id="decideNow" ${voted ? '' : 'disabled'}>Decide now</button>` : ''}</div></section>`;
}
function resultCard(){
  const r = D.result;
  return `<section class="vote"><div class="stamp tilt slam ${r.ok ? 'green' : ''}">${r.ok ? 'Approved' : 'Not quite'}</div><h3>${r.team ? 'The team chose' : 'You chose'}</h3>
    <h2>${esc(r.choice)}</h2><div class="why ${r.ok ? 'good' : ''}" style="font-size:19px">${esc(r.why)}</div>
    ${r.count && r.team ? `<p class="muted" style="color:var(--ink2)">Votes: ${r.opts.map((o, k) => `${'ABC'[k]} ${r.count[k]}`).join(' · ')}</p>` : ''}
    <div class="vfoot"><span></span><button class="btn gold" id="resultGo">${r.ok ? 'Continue ▶' : 'Vote again'}</button></div></section>`;
}

/* ---------- bindings ---------- */
function bindBench(x, pr, allDone, missing){
  const b = $('bench');
  const pad = $('pad'); if (pad) pad.onclick = e => { const k = e.target.closest('[data-n]'); if (k) typeDigit(k.dataset.n === 'del' ? 'del' : k.dataset.n); };
  if ($('runMachine')) $('runMachine').onclick = () => runMachine(x.id);
  b.querySelectorAll('.grp').forEach(el => el.onclick = () => { const k = +el.dataset.g;
    if (!pr.done[k] && !D.machineRun) { pr.gi = k; pr.typed = ''; pr.flash = null; SC.sfx.click(); renderBench(); }
    else if (pr.done[k]) { D.hit = x.groups[k].code; showTab('book'); renderBook(true); } });
  b.querySelectorAll('[data-guess]').forEach(el => el.onclick = () => { SC.sfx.click(); G().act({t:'recover', word:missing[0], guess:el.dataset.guess}); });
  if ($('fileBtn')) $('fileBtn').onclick = () => { $('fileBtn').disabled = true; SC.sfx.stamp(); G().act({t:'file', iid:x.id}); };
  if (!allDone && pr.typed === '' && !pr.flash && pr.done.every(d => !d)) D.say(SC.SAY.stripFirst, lvl().showMath ? 'Use the number pad, or the keys on your keyboard.' : '');
  else if (allDone && missing.length) D.say(SC.SAY.unknown);
  else if (allDone) D.say(SC.SAY.read);
}
function bindVote(ph){
  $('bench').querySelectorAll('[data-opt]').forEach(el => el.onclick = () => { SC.sfx.click(); G().act({t:'vote', opt:+el.dataset.opt}); });
  if ($('decideNow')) $('decideNow').onclick = () => G().act({t:'decide'});
  D.say(G().mode === 'solo' ? SC.SAY.vote : SC.SAY.teamVote);
}
function bindResult(){ $('resultGo').onclick = () => { SC.sfx.click(); D.result = null; D.render(); G().afterResult(); }; }
document.addEventListener('click', e => { if (e.target.id === 'tryTake') G().act({t:'take'}); });

/* ---------- the codebook ---------- */
function renderBook(scroll){
  const g = G(); if (!g.st) return;
  const st = g.st, B = g.B, q = (D.search || '').trim().toUpperCase();
  const used = new Set(B.intercepts.flatMap(x => x.words));
  const rows = SC.ALL_WORDS.map(w => ({w, code:B.book[w], unk:!E.known(st, B, w), rec:st.recovered[w]}))
    .filter(r => (!r.unk || used.has(r.w)) && (!q || r.code.startsWith(q) || (!r.unk && r.w.includes(q))))
    .sort((a, b) => a.code.localeCompare(b.code));
  $('bookTab').innerHTML = `<div class="book ${scroll ? 'flip' : ''}"><h4><span>JN-25 codebook</span><span>${rows.filter(r => !r.unk).length} words</span></h4>
    <input class="booksearch" id="bookSearch" placeholder="Search a number or word" value="${esc(D.search || '')}" inputmode="search" autocomplete="off">
    <div class="bookrows">${rows.map(r => `<span class="g ${r.code === D.hit ? 'hit' : ''}" ${r.code === D.hit ? 'id="bookHit"' : ''}>${r.code}</span><span class="${r.unk ? 'unk' : r.rec ? 'new' : ''} ${r.code === D.hit ? 'hit' : ''}">${r.unk ? '?????' : esc(r.w)}${r.rec ? ` <small>· found by ${esc(pidName(r.rec))}</small>` : ''}</span>`).join('')}</div></div>`;
  const s = $('bookSearch'); s.oninput = () => { D.search = s.value; D.hit = null; const pos = s.selectionStart; renderBook(); $('bookSearch').focus(); $('bookSearch').setSelectionRange(pos, pos); };
  s.onkeydown = e => e.stopPropagation();
  if (scroll && $('bookHit')) $('bookHit').scrollIntoView({block:'center', behavior:'smooth'});
}
/* ---------- the board ---------- */
function renderBoard(){
  const g = G(); if (!g.st) return;
  const st = g.st, B = g.B, {m} = E.find(st.mid), filed = Object.keys(st.filed);
  const keys = filed.filter(id => B.byId[id].key), fill = filed.filter(id => !B.byId[id].key);
  const team = g.mode !== 'solo', by = id => team ? ` · filed by ${esc(pidName(st.filed[id]))}` : '';
  $('boardCount').textContent = filed.length;
  $('boardTab').innerHTML = `<div class="board">${keys.length ? keys.map(id => `<div class="fact ${D.newFact === id ? 'new' : ''}">${esc(m.messages[id].fact || m.messages[id].plain)}<small>${esc(m.messages[id].words.join(' '))}${by(id)}</small></div>`).join('')
    : '<p class="empty">Decoded priority messages are pinned here.</p>'}
    ${fill.length ? `<div class="fact small">${fill.length} everyday message${fill.length > 1 ? 's' : ''} read: weather, fuel and supply reports. Every one teaches us the enemy's habits.</div>` : ''}</div>`;
}
const showTab = t => { D.tab = t; document.querySelectorAll('.tab').forEach(b => b.classList.toggle('on', b.dataset.tab === t)); $('bookTab').hidden = t !== 'book'; $('boardTab').hidden = t !== 'board'; };
/* On phones the side panel is a drawer: tap a tab to open it, tap the open tab again to close it. */
const narrow = () => matchMedia('(max-width:860px)').matches;
document.querySelector('.tabs').onclick = e => { const b = e.target.closest('.tab'); if (!b) return; const side = document.querySelector('.side');
  if (narrow() && b.dataset.tab === D.tab) side.classList.toggle('open'); else { showTab(b.dataset.tab); side.classList.add('open'); } SC.sfx.flip(); };
D.showTab = showTab;

/* ---------- clock, crew and news ---------- */
function renderClock(){
  const st = G().st; if (!st) return; const d = E.clock(st), el = $('clock');
  $('clockTime').textContent = `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`;
  $('clockDate').textContent = d.toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
  const left = st.limit ? Math.max(0, st.limit - st.t) / st.limit : 1;
  $('ringFill').style.strokeDashoffset = 106.8 * (1 - left);
  el.classList.toggle('off', !st.limit); el.classList.toggle('late', !!st.late); el.classList.toggle('warn', !!st.limit && !st.late && left < .2 && !st.done);
  el.title = st.limit ? (st.late ? 'Time is up: finish anyway' : `${Math.ceil((st.limit - st.t) / 60)} min left`) : 'No clock at this level';
  SC.music.setMode(st.limit && !st.late && !st.done && left < .2 ? 'tense' : 'calm');
}
function renderCrew(){
  const g = G(), el = $('crewBar'); if (g.mode === 'solo') { el.innerHTML = ''; return; }
  const ps = g.players().filter(p => p.connected !== false), ph = E.phase(g.st);
  el.innerHTML = ps.slice(0, 12).map(p => UI.avatar(p, ph && ph.k === 'vote' ? (g.st.votes[p.pid] != null ? 'voted' : '') : (g.st.assign[p.pid] ? 'busy' : ''))).join('') + (ps.length > 12 ? `<span class="more">+${ps.length - 12}</span>` : '');
}
D.clock = () => { renderClock(); };
D.news = (text, icon) => {
  const tape = $('tape'); tape.querySelectorAll('.line').forEach(l => { l.classList.remove('new'); const c = l.querySelector('.cur'); if (c) c.remove(); });
  const line = document.createElement('span'); line.className = 'line new'; line.innerHTML = `<span class="ic">${SC.NEWS_ICON[icon] || '📻'}</span><span class="tx"></span><span class="cur"></span>`;
  tape.prepend(line); while (tape.children.length > 6) tape.lastChild.remove();
  SC.sfx.teletype(8); UI.typeOut(line.querySelector('.tx'), text.toUpperCase(), null, 30);
};

/* ---------- events from the host ---------- */
D.onEvent = ev => {
  const g = G(), mine = ev.pid === g.myPid;
  switch (ev.t) {
    case 'wrongGuess': if (mine) { g.stats.slips++; D.why = {word:ev.word, guess:ev.guess, text:ev.why}; SC.sfx.bad(); D.say(SC.SAY.wrongTarget, ev.why); } break;
    case 'recovered':
      D.why = null;
      if (mine && !ev.again) { SC.sfx.ok(); UI.notify(SC.reward(me(), 'recovered', 1, SC.XP.recover)); UI.toast('📖', `New word: ${ev.word}`, 'Added to the codebook for the whole station.'); }
      else if (!mine) UI.toast('📖', `${pidName(ev.pid)} worked out a word`, `${g.B.book[ev.word]} = ${ev.word}`);
      D.hit = g.B.book[ev.word]; break;
    case 'filed':
      D.newFact = ev.iid;
      if (mine) { const p = me(); UI.notify(SC.reward(p, 'filed', 1, 0)); UI.notify(ev.key ? SC.reward(p, 'keys', 1, SC.XP.key) : SC.reward(p, 'filler', 1, SC.XP.filler));
        UI.toast('📌', ev.key ? 'Priority message filed' : 'Message filed', ev.fact || 'Pinned on the board.'); showTab('board'); }
      else if (ev.key) UI.toast('📌', `${pidName(ev.pid)} filed a priority message`, ev.fact || '');
      break;
    case 'assigned': if (mine) { D.waiting = false; } break;
    case 'nothing': if (mine) D.waiting = Object.values(g.st.assign).length > 0; break;
    case 'news': D.news(ev.text, ev.icon); break;
    case 'late': UI.toast('⏱', 'Time is up!', 'Keep going: finish the mission anyway.'); SC.sfx.bad(); break;
    case 'voteResult': {
      const ph = E.find(g.st.mid).m.phases.find(p => p.id === ev.id);
      D.result = {ok:ev.ok, why:ev.why, choice:ph.opts[ev.opt].t, count:ev.count, opts:ph.opts, team:g.mode !== 'solo'};
      if (ev.ok) { SC.sfx.stamp(); setTimeout(SC.sfx.ok, 200); if (g.myVote === ev.opt) UI.notify(SC.reward(me(), 'votesRight', 1, SC.XP.vote)); }
      else { SC.sfx.bad(); g.stats.slips += g.myVote === ev.opt ? 1 : 0; }
      break; }
  }
};

/* ---------- keyboard and hints ---------- */
document.addEventListener('keydown', e => {
  if ($('scrDesk').hidden || UI.modalOpen() || UI.folderOpen() || e.ctrlKey || e.metaKey || e.altKey) return;
  if (/^[0-9]$/.test(e.key)) { typeDigit(e.key); e.preventDefault(); }
  else if (e.key === 'Backspace') { typeDigit('del'); e.preventDefault(); }
  else if (e.key === 'Enter' && $('fileBtn')) $('fileBtn').click();
  else if (e.key === 'Enter' && $('resultGo')) $('resultGo').click();
});
$('hintBtn').onclick = () => {
  const g = G(), st = g.st; if (!st) return; const ph = E.phase(st); if (!ph) return;
  g.stats.hints++; UI.notify(SC.reward(me(), 'hintsUsed', 1, 0)); SC.sfx.click();
  if (ph.k === 'vote') { const wrong = ph.opts.map((o, k) => k).filter(k => !ph.opts[k].ok), key = ph.id + ':' + st.round;
    if (D.voteHidden[key] == null) { D.voteHidden[key] = wrong[0]; D.say(`Answer ${'ABC'[wrong[0]]} is not it:`, ph.opts[wrong[0]].why); renderBench(); } else D.say('Read each answer and ask: does it fit what we know?'); return; }
  const iid = st.assign[g.myPid]; if (!iid) return D.say('Look at the board: every pinned card is something we know.');
  const pr = prog(iid), x = g.B.byId[iid], miss = E.missing(st, g.B, iid);
  if (!pr.done.every(Boolean)) { const grp = x.groups[pr.gi]; D.say(C.hints({cipher:grp.cipher, add:grp.add, typed:pr.typed, tries:2})); return; }
  if (miss.length) { const tg = E.find(st.mid).m.targets[miss[0]], wrong = tg.opts.filter(o => o !== miss[0]), key = 'w:' + miss[0];
    if (!D.voteHidden[key]) { D.voteHidden[key] = wrong[0]; D.say(`It is not ${wrong[0]}.`, tg.why[wrong[0]]); renderBench(); } else D.say(tg.clue); return; }
  D.say(SC.SAY.read);
};
$('sayBtn').onclick = () => { if (SC.Store.settings.voice !== false && D.said) SC.speech.say(D.said); };
})();

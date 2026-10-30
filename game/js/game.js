/* The game controller: solo play, hosting and joining a team game, the mission clock, rewards and the end of a
   mission. As in Crater Crew, the host's browser is the server: it applies every action with the mission rules and
   sends the new shared state to everyone. In solo play this device is its own host. */
(function () {
const SC = window.SC, UI = SC.UI, {$, esc} = UI, E = SC.Engine, D = SC.Desk;
SC.VERSION = 1;
const G = SC.Game = {mode:null, myPid:null, st:null, B:null, net:null, code:null, lobby:null, cid2pid:{}, stats:{hints:0, slips:0}, myVote:null, timer:null, pendingDone:false};
const me = () => SC.Store.current();
const isHost = () => G.mode === 'solo' || G.mode === 'host';
G.players = () => G.mode === 'solo' ? [SC.playerSummary(me())] : ((G.lobby && G.lobby.players) || []);
const connected = () => G.players().filter(p => p.connected !== false);

/* ---------- screens ---------- */
G.home = () => { leave(); UI.renderHome(); UI.show('scrHome'); };
G.map = () => { stopTimer(); G.st = null; SC.Map.render(); UI.show('scrMap'); };
G.openMission = mid => UI.briefing(mid, () => startSolo(mid));
function leave(){
  stopTimer(); if (G.net) { try { G.net.close(); } catch (e) {} }
  clearInterval(G.pingTimer);
  Object.assign(G, {mode:null, net:null, code:null, lobby:null, cid2pid:{}, st:null, B:null, pendingDone:false});
  UI.closeFolder(); UI.closeModal();
}

/* ---------- running a mission ---------- */
function startSolo(mid){
  const p = me(); G.mode = 'solo'; G.myPid = p.id;
  const seed = (Date.now() ^ (Math.random() * 1e9)) >>> 0;
  G.st = E.newState(mid, seed, {n:1, level:p.level}); G.B = E.build(mid, seed, 1);
  begin();
}
function begin(){
  D.reset(); G.stats = {hints:0, slips:0}; G.myVote = null; G.pendingDone = false;
  UI.show('scrDesk'); D.showTab('book'); D.enter();
  if (isHost()) startTimer();
  G.act({t:'take'});
}
G.act = a => { if (!G.st) return; if (a.t === 'vote') G.myVote = a.opt; if (G.mode === 'client') G.net.send({type:'act', a}); else hostApply(G.myPid, a); };
function hostApply(pid, a){
  const st = G.st, B = G.B; if (!st || st.done) return;
  let ev = [];
  switch (a.t) {
    case 'take': ev = E.take(st, B, pid); break;
    case 'recover': ev = E.recover(st, B, pid, String(a.word), String(a.guess)); break;
    case 'file': ev = E.file(st, B, pid, String(a.iid)); break;
    case 'vote': ev = E.vote(st, pid, a.opt | 0); if (ev.length) setTimeout(() => maybeClose(st.phase, st.round), G.mode === 'solo' ? 350 : 900); break;
    case 'decide': if (pid === G.myPid) ev = E.closeVote(st); break;
  }
  if (ev.length) dispatch(ev);
}
/* Close the vote once everyone still connected has voted. */
function maybeClose(phase, round){
  const st = G.st; if (!st || st.phase !== phase || st.round !== round) return;
  if (connected().every(p => st.votes[p.pid] != null)) dispatch(E.closeVote(st));
}
function dispatch(ev){
  if (G.mode === 'host') G.net.broadcast({type:'ev', ev, st:G.st});
  handle(ev);
}
function handle(ev){
  ev.forEach(e => {
    D.onEvent(e);
    if (e.t === 'phase') { G.myVote = null; if (!D.result && E.phase(G.st) && E.phase(G.st).k === 'decode') setTimeout(() => G.act({t:'take'}), 50); }
    if (e.t === 'filed' && e.pid === G.myPid) setTimeout(() => G.act({t:'take'}), 700);
    if (e.t === 'voteResult' && !e.ok) G.myVote = null;
    if (e.t === 'done') { if (D.result) G.pendingDone = true; else setTimeout(finish, 900); }
  });
  D.render();
}
G.afterResult = () => {
  if (G.pendingDone || (G.st && G.st.done)) { G.pendingDone = false; finish(); return; }
  const ph = E.phase(G.st); if (ph && ph.k === 'decode' && !G.st.assign[G.myPid]) G.act({t:'take'});
};
/* The mission clock only runs while messages are being decoded, and not while the host reads a folder. */
function startTimer(){ stopTimer(); G.timer = setInterval(() => {
  const st = G.st; if (!st || st.done) return; const ph = E.phase(st);
  if (!ph || ph.k !== 'decode' || UI.folderOpen()) return;
  const ev = E.tick(st, 1);
  if (ev.length) dispatch(ev); else { if (G.mode === 'host') G.net.broadcast({type:'t', t:st.t}); D.clock(); }
}, 1000); }
function stopTimer(){ clearInterval(G.timer); G.timer = null; }
function finish(){
  const st = G.st; if (!st || G.finished === st) return; G.finished = st; stopTimer();
  const p = me(), team = G.mode !== 'solo', stars = E.stars(G.stats, st.late), xp0 = p.xp;
  const notices = SC.finishMission(p, st.mid, stars, {team, early:!!st.limit && st.t <= st.limit / 2, late:st.late});
  const gains = [`+${p.xp - xp0} XP this mission`, `${SC.rankInfo(p).name}`];
  notices.forEach(n => { if (n.k === 'patch') gains.push('Patch: ' + SC.PATCHES.find(x => x.id === n.id).name); });
  gains.push(`Records Room: ${SC.PEOPLE[E.find(st.mid).m.history.person].name}`);
  UI.outcome({mid:st.mid, result:st.done, stars, gains, team, onDone:() => {
    UI.notify(notices);
    if (G.mode === 'solo') { G.mode = null; G.map(); }
    else if (G.mode === 'host') { G.st = null; G.net.broadcast({type:'toLobby', lobby:G.lobby}); enterLobby(); }
    else { G.st = null; enterLobby(); }
  }});
}

/* ---------- menu on the workstation ---------- */
$('deskMenu').onclick = () => {
  UI.openModal(`<div class="sh"><h2>Menu</h2><button class="xbtn" data-close aria-label="Close">×</button></div><div class="sb" style="display:flex;flex-direction:column;gap:10px">
    <button class="big" data-close><span class="ic">▶</span><span><b>Back to work</b></span></button>
    <button class="big" id="mnBrief"><span class="ic">📁</span><span><b>Read the briefing again</b></span></button>
    <button class="big" id="mnSet"><span class="ic">⚙</span><span><b>Settings</b></span></button>
    <button class="big" id="mnLeave"><span class="ic">🚪</span><span><b>${G.mode === 'solo' ? 'Leave the mission' : 'Leave the team game'}</b><small>${G.mode === 'solo' ? 'Your progress in this mission is lost.' : G.mode === 'host' ? 'Everyone else is sent home too.' : 'You can join again with the code.'}</small></span></button></div>`, true);
  $('mnBrief').onclick = () => { UI.closeModal(); const {m} = E.find(G.st.mid); UI.folder('BRIEFING', `<div class="paper"><h2>${esc(m.title)}</h2>
    <div class="speech" style="margin-top:14px">${UI.mentorAvatar('lg')}<div class="bubble">${m.briefing.map(t => `<p>${esc(t)}</p>`).join('')}</div></div><div class="goal">${esc(m.goal)}</div>
    <div class="acts"><button class="btn gold" id="brClose">Back to work</button></div></div>`); $('brClose').onclick = UI.closeFolder; };
  $('mnSet').onclick = UI.settings;
  $('mnLeave').onclick = () => { UI.closeModal(); if (G.mode === 'solo') { G.mode = null; G.map(); } else G.home(); };
};

/* ---------- hosting ---------- */
function startHost(){
  const p = me(); if (!p) return;
  G.mode = 'host'; G.myPid = p.id; G.code = SC.makeRoomCode(); G.cid2pid = {};
  const c = SC.CAMPAIGNS[0], open = c.missions.filter((m, i) => SC.missionOpen(p, c, i));
  G.lobby = {players:[{...SC.playerSummary(p), connected:true, host:true}], mid:(open.find(m => !(p.missions[m.id] || {}).done) || open[open.length - 1]).id, level:'codebreaker'};
  $('netStatus').textContent = 'Opening room…';
  G.net = SC.Net.host(G.code, {
    onOpen:() => { $('netStatus').textContent = 'Room open: the class can join'; renderLobby(); },
    onError:e => { if (e === 'taken') { G.net.close(); startHost(); return; } $('netStatus').textContent = 'Not connected'; UI.toast('⚠', 'Could not open the room', SC.Net.errorText(e), 8000); },
    onConnect:() => {},
    onDisconnect:cid => { const pid = G.cid2pid[cid]; delete G.cid2pid[cid]; if (pid && !Object.values(G.cid2pid).includes(pid)) playerGone(pid); },
    onMessage:(cid, m) => hostMessage(cid, m),
  });
  keepAwake(); enterLobby();
}
async function keepAwake(){ try { if ('wakeLock' in navigator) G.wake = await navigator.wakeLock.request('screen'); } catch (e) {} }
document.addEventListener('visibilitychange', () => { if (G.mode === 'host' && document.visibilityState === 'visible') keepAwake(); });
const lobbyMsg = () => ({type:'lobby', lobby:G.lobby, code:G.code});
function hostMessage(cid, m){
  if (!m || typeof m !== 'object') return;
  if (m.type === 'ping') { G.net.send(cid, {type:'pong', t:m.t}); return; }
  if (m.type === 'hello') {
    if (m.v !== SC.VERSION) { G.net.send(cid, {type:'error', text:'This device has a different version of the game. Reload the page on both devices.'}); return; }
    const pl = m.player || {}; if (!pl.pid) return;
    const known = G.lobby.players.find(x => x.pid === pl.pid);
    if (!known && G.lobby.players.length >= 33) { G.net.send(cid, {type:'error', text:'This game already has 32 players.'}); return; }
    G.cid2pid[cid] = pl.pid;
    const entry = {pid:pl.pid, name:String(pl.name || 'Cadet').slice(0, 16), color:pl.color, avatar:pl.avatar ?? null, level:SC.LEVELS[pl.level] ? pl.level : 'codebreaker', rank:pl.rank | 0, connected:true};
    if (known) Object.assign(known, entry); else G.lobby.players.push(entry);
    SC.sfx.join(); G.net.broadcast(lobbyMsg());
    if (G.st) G.net.send(cid, {type:'start', mid:G.st.mid, seed:G.st.seed, n:G.st.n, st:G.st, lobby:G.lobby});
    renderLobby(); D.render && G.st && D.render(); return;
  }
  const pid = G.cid2pid[cid]; if (!pid) return;
  if (m.type === 'act' && m.a && typeof m.a === 'object' && m.a.t !== 'decide') hostApply(pid, m.a);
}
function playerGone(pid){
  const lp = G.lobby && G.lobby.players.find(x => x.pid === pid); if (!lp) return;
  lp.connected = false; G.net.broadcast(lobbyMsg());
  if (G.st) { Object.keys(G.st.taken).forEach(id => { G.st.taken[id] = G.st.taken[id].filter(x => x !== pid); }); delete G.st.assign[pid];
    G.net.broadcast({type:'ev', ev:[], st:G.st}); maybeClose(G.st.phase, G.st.round); D.render(); }
  renderLobby();
}
function kick(pid){
  Object.entries(G.cid2pid).forEach(([cid, p]) => { if (p === pid) { G.net.send(cid, {type:'kicked'}); delete G.cid2pid[cid]; setTimeout(() => G.net.drop(cid), 300); } });
  G.lobby.players = G.lobby.players.filter(p => p.pid !== pid); G.net.broadcast(lobbyMsg()); renderLobby();
}
function startTeam(){
  const L = G.lobby, n = Math.max(1, connected().length), seed = (Date.now() ^ (Math.random() * 1e9)) >>> 0;
  G.st = E.newState(L.mid, seed, {n, level:L.level}); G.B = E.build(L.mid, seed, n);
  G.net.broadcast({type:'start', mid:L.mid, seed, n, st:G.st, lobby:L});
  teamBegin();
}
function teamBegin(){
  begin();
  const {m, i} = E.find(G.st.mid);
  UI.folder('MISSION ' + (i + 1), `<div class="paper"><div class="stamp corner tilt slam">Top Secret</div><h2>${esc(m.title)}</h2>
    <div class="meta"><span>📅 ${esc(m.date)}</span><span>📍 ${esc(m.place)}</span><span>👥 ${connected().length} on duty</span></div>
    <div class="speech">${UI.mentorAvatar('lg')}<div class="bubble">${m.briefing.map(t => `<p>${esc(t)}</p>`).join('')}</div></div><div class="goal">${esc(m.goal)}</div>
    <div class="acts"><button class="btn" id="tbSay">🔊 Read aloud</button><button class="btn gold" id="tbGo">To my desk ▶</button></div></div>`);
  SC.sfx.stamp();
  $('tbSay').onclick = () => SC.speech.say(m.briefing.join(' ') + ' Your goal: ' + m.goal);
  $('tbGo').onclick = () => { UI.closeFolder(); SC.sfx.morse(); };
}

/* ---------- joining ---------- */
function joinGame(raw){
  const p = me(), code = SC.cleanCode(raw); $('joinErr').hidden = true;
  if (!p) return; if (code.length !== 4) { $('joinErr').hidden = false; $('joinErr').textContent = 'The code has 4 letters or numbers, like SPY-K7QF.'; return; }
  G.mode = 'client'; G.myPid = p.id; G.code = code; G.lobby = {players:[], mid:null, level:'codebreaker'};
  $('joinBtn').disabled = true; $('joinBtn').querySelector('b').textContent = 'Joining…';
  G.net = SC.Net.join(code, {
    onOpen:() => { G.net.send({type:'hello', v:SC.VERSION, player:SC.playerSummary(p)}); startPing(); },
    onMessage:m => clientMessage(m),
    onClose:() => lost(),
    onError:e => failed(SC.Net.errorText(e)),
  });
}
function startPing(){ clearInterval(G.pingTimer); G.pingTimer = setInterval(() => { if (G.net) G.net.send({type:'ping', t:performance.now()}); }, 4000); }
function failed(text){ const c = G.code; G.home(); $('joinCode').value = c ? 'SPY-' + c : ''; $('joinErr').hidden = false; $('joinErr').textContent = text; resetJoinBtn(); }
function lost(){ if (G.mode !== 'client') return; const c = G.code; G.home(); $('joinCode').value = 'SPY-' + c; resetJoinBtn();
  UI.toast('📡', 'Lost the connection', 'Tap Join to get back in: your messages are waiting.', 8000); }
const resetJoinBtn = () => { $('joinBtn').disabled = !me() || !SC.netAvailable(); $('joinBtn').querySelector('b').textContent = 'Join'; };
function clientMessage(m){
  switch (m.type) {
    case 'pong': G.ping = Math.round(performance.now() - m.t); break;
    case 'error': failed(m.text); break;
    case 'kicked': G.home(); UI.toast('🚪', 'You left the game', 'The host removed you from this game.', 8000); break;
    case 'lobby': G.lobby = m.lobby; resetJoinBtn(); if (!G.st) enterLobby(); else D.render(); break;
    case 'toLobby': G.lobby = m.lobby; if (!G.st || G.st.done) { if (!UI.folderOpen()) { G.st = null; enterLobby(); } } break;
    case 'start': { G.lobby = m.lobby || G.lobby; const rejoin = G.st && G.st.mid === m.mid && G.st.seed === m.seed;
      G.st = m.st; G.B = E.build(m.mid, m.seed, m.n); G.finished = null;
      if (rejoin) { D.render(); break; } teamBegin(); break; }
    case 'ev': if (!G.B) break; G.st = m.st; handle(m.ev); break;
    case 't': if (G.st) { G.st.t = m.t; D.clock(); } break;
  }
}

/* ---------- lobby ---------- */
function enterLobby(){ UI.show('scrLobby'); renderLobby(); }
function renderLobby(){
  if ($('scrLobby').hidden || !G.lobby) return;
  const host = G.mode === 'host', L = G.lobby, url = location.href.split('?')[0].split('#')[0] + '?join=' + G.code;
  $('roomCode').textContent = 'SPY-' + (G.code || '····');
  if (host && window.qrcode && G.qrFor !== url) { try { const qr = window.qrcode(0, 'M'); qr.addData(url); qr.make(); $('qr').innerHTML = qr.createSvgTag({cellSize:4, margin:2, scalable:true}); G.qrFor = url; } catch (e) { $('qr').hidden = true; } }
  $('qr').hidden = !host;
  $('roomHelp').innerHTML = host ? 'On the other devices: open Spy Cadet, make an ID badge, tap <b>Join</b> and type this code. Or scan the QR code.' : 'You are in! The host picks the mission and starts it.';
  if (!host) $('netStatus').textContent = `Connected to SPY-${G.code}${G.ping ? ` · ${G.ping} ms` : ''}`;
  $('crewCount').textContent = connected().length;
  $('crewList').innerHTML = L.players.map(p => `<li class="${p.connected === false ? 'off' : ''}">${UI.avatar(p)}<span><b>${esc(p.name)}</b>${p.pid === G.myPid ? ' (you)' : ''}<small>${p.host ? 'Host · ' : ''}${esc((SC.LEVELS[p.level] || {}).label || '')}${p.connected === false ? ' · away' : ''}</small></span>
    ${host && !p.host ? `<button class="kick" data-kick="${p.pid}" aria-label="Remove ${esc(p.name)}">✕</button>` : ''}</li>`).join('');
  $('hostPanel').hidden = !host;
  if (host) { const p = me(), c = SC.CAMPAIGNS[0];
    $('lobbyMissions').innerHTML = c.missions.map((m, i) => { const open = SC.missionOpen(p, c, i);
      return `<label style="${open ? '' : 'opacity:.45'}"><input type="radio" name="lm" value="${m.id}" ${m.id === L.mid ? 'checked' : ''} ${open ? '' : 'disabled'}><span><b>${i + 1}. ${esc(m.title)}</b><br><small class="muted">${esc(m.date)}</small></span></label>`; }).join('');
    $('lobbyClock').value = L.level; }
}
$('lobbyMissions').onchange = e => { if (e.target.name === 'lm') { G.lobby.mid = e.target.value; G.net.broadcast(lobbyMsg()); } };
$('lobbyClock').onchange = e => { G.lobby.level = e.target.value; G.net.broadcast(lobbyMsg()); };
$('crewList').onclick = e => { const b = e.target.closest('[data-kick]'); if (b && G.mode === 'host') kick(b.dataset.kick); };
$('startTeam').onclick = () => { SC.sfx.stamp(); startTeam(); };
$('lobbyLeave').onclick = () => G.home();

/* ---------- home buttons ---------- */
$('soloBtn').onclick = () => { if (!me()) return; SC.sfx.click(); G.map(); };
$('hostBtn').onclick = () => { if (!me()) return; SC.sfx.click(); startHost(); };
$('joinBtn').onclick = () => joinGame($('joinCode').value);
$('joinCode').onkeydown = e => { if (e.key === 'Enter') joinGame($('joinCode').value); };
$('joinCode').oninput = e => { const v = SC.cleanCode(e.target.value); if (v.length === 4 && e.target.value.length >= 4) e.target.value = 'SPY-' + v; };

/* ---------- start ---------- */
const q = new URLSearchParams(location.search);
if (q.get('join')) $('joinCode').value = 'SPY-' + SC.cleanCode(q.get('join'));
UI.renderHome(); UI.show('scrHome');
if (!SC.Store.profiles().length) setTimeout(() => UI.profileModal(null), 400);
})();

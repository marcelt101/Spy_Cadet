/* Networking. The host's browser is the server; three ways for devices to reach it:
   - relay (school-safe): every message goes through the classroom server (server/relay.js) over ordinary HTTPS,
     by WebSocket when the network allows it, otherwise by long-polling. Used whenever a classroom server is set
     (js/config.js, or ?relay=https://… in the link). School firewalls that block WebRTC do not block this.
   - PeerJS (from Crater Crew): devices find each other through the PeerJS service, then talk directly over WebRTC.
     Used when no classroom server is set, or with ?net=peer.
   - "?net=local": a BroadcastChannel, for testing several windows of one browser on one computer. */
(function () {
const SC = window.SC = window.SC || {};
const PREFIX = 'spy-cadet-v1-';
const ALPHA = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
SC.makeRoomCode = () => { let s = ''; for (let i=0;i<4;i++) s += ALPHA[Math.floor(Math.random()*ALPHA.length)]; return s; };
SC.cleanCode = c => String(c||'').toUpperCase().replace(/^SPY-?/,'').replace(/[^A-Z0-9]/g,'').slice(0,4);
const Q = () => new URLSearchParams(location.search);
const useLocal = () => Q().get('net') === 'local';
const relayBase = () => (Q().get('relay') || SC.RELAY_URL || (Q().get('net') === 'relay' ? location.origin : '')).replace(/\/+$/, '');
const mode = () => useLocal() ? 'local' : Q().get('net') === 'peer' ? 'peer' : relayBase() ? 'relay' : 'peer';
/* Optional self-hosted PeerJS server, e.g. ?peerhost=192.168.1.20&peerport=9000 */
const peerOpts = () => { const q = Q(), o = {debug:0};
  if (q.get('peerhost')) { o.host = q.get('peerhost'); o.port = +(q.get('peerport') || 9000); o.path = q.get('peerpath') || '/'; o.secure = q.get('peersecure') === '1'; }
  return o; };
SC.netMode = mode;
SC.netAvailable = () => mode() === 'local' || (mode() === 'relay' ? typeof fetch === 'function' : typeof window.Peer === 'function');
const wait = ms => new Promise(r => setTimeout(r, ms));
const hostName = u => { try { return new URL(u).host; } catch (e) { return u; } };

/* ---------- relay: the classroom server passes messages; numbered and confirmed, so short drops lose nothing ---------- */
function relayLink(base, role, room, h){
  const via = Q().get('via'); // ?via=poll tests the backup way
  const L = {via:null, cid:null};
  let token = null, seq = 0, cseq = 0, unacked = [], ws = null, ended = false, quiet = false, sending = false, polling = false;
  let lastOk = Date.now(), beat = null;
  const post = (path, body) => fetch(base + '/relay/' + path, {method:'POST', body:JSON.stringify(body), headers:{'content-type':'text/plain'}, cache:'no-store'})
    .then(r => r.json().then(j => ({status:r.status, j})));
  function got(b){
    lastOk = Date.now(); if (!b) return;
    if (b.ack != null) unacked = unacked.filter(m => m.cseq > b.ack);
    (b.msgs || []).forEach(m => { if (m.seq <= seq) return; seq = m.seq; if (m.op === 'close') end('closed'); else if (!ended) h.onMsg(m); });
  }
  function end(why){
    if (ended) return; ended = true; clearInterval(beat);
    if (ws) { try { ws.close(); } catch (e) {} ws = null; }
    if (!quiet) h.onEnd(why);
  }
  function send(m){
    if (ended) return; m.cseq = ++cseq; unacked.push(m);
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ack:seq, msgs:[m]})); else flushPost();
  }
  async function flushPost(){
    if (ws || sending || ended || !token || !unacked.length) return;
    sending = true;
    try { const r = await post('send?token=' + token, {ack:seq, msgs:unacked.slice()}); if (r.status === 410) { sending = false; return end('gone'); } got({ack:r.j.ack}); }
    catch (e) { await wait(1000); }
    sending = false; if (unacked.length) flushPost();
  }
  async function poll(){
    if (polling) return; polling = true;
    while (!ended && !ws) {
      try { const r = await fetch(base + '/relay/poll?token=' + token + '&ack=' + seq, {cache:'no-store'}), j = await r.json();
        if (r.status === 410) { end('gone'); break; } got(j); }
      catch (e) { await wait(1500); }
    }
    polling = false;
  }
  function tryWs(){
    return new Promise(done => {
      if (via === 'poll' || typeof WebSocket !== 'function') return done(false);
      let s, ok = false; try { s = new WebSocket(base.replace(/^http/, 'ws') + '/relay/ws?token=' + token); } catch (e) { return done(false); }
      const t = setTimeout(() => { if (!ok) { try { s.close(); } catch (e) {} done(false); } }, 4000);
      s.onmessage = e => { let b; try { b = JSON.parse(e.data); } catch (x) { return; }
        if (!ok) { ok = true; clearTimeout(t); ws = s; L.via = 'websocket'; done(true); }
        got(b);
        if (ws === s && unacked.length && b.msgs) s.send(JSON.stringify({ack:seq, msgs:unacked})); // first frame: resend anything unconfirmed
        else if (ws === s && b.msgs && b.msgs.length) s.send(JSON.stringify({ack:seq}));
      };
      s.onclose = s.onerror = () => { clearTimeout(t); if (!ok) { ok = true; return done(false); }
        if (ws === s) { ws = null; if (!ended) { L.via = 'long-poll'; poll(); flushPost(); } } }; // carry on the backup way
    });
  }
  (async () => {
    let r; try { r = await post('open', {role, room}); } catch (e) { return h.onError('offline'); }
    if (r.status !== 200) return h.onError(r.j && r.j.error || 'offline');
    token = r.j.token; L.cid = r.j.cid || null;
    beat = setInterval(() => {
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ack:seq}));
      if (Date.now() - lastOk > 35000) end('offline');
    }, 10000);
    h.onOpen(); flushPost();
    if (!(await tryWs()) && !ended) { L.via = 'long-poll'; poll(); flushPost(); }
  })();
  addEventListener('pagehide', () => { if (token && !ended && navigator.sendBeacon) navigator.sendBeacon(base + '/relay/send?token=' + token, JSON.stringify({ack:seq, msgs:[{cseq:++cseq, op:'leave'}]})); });
  L.send = send;
  L.close = () => { if (ended) return; quiet = true; send({op:'leave'}); setTimeout(() => end('left'), 400); };
  return L;
}
function relayHost(code, h){
  const conns = new Set();
  const link = relayLink(relayBase(), 'host', code, {
    onOpen:() => h.onOpen(), onError:e => h.onError(e),
    onMsg:m => { if (m.op === 'connect') { conns.add(m.cid); h.onConnect(m.cid); }
      else if (m.op === 'disconnect') { if (conns.delete(m.cid)) h.onDisconnect(m.cid); }
      else if (m.op === 'data' && conns.has(m.from)) h.onMessage(m.from, m.data); },
    onEnd:() => { conns.forEach(c => h.onDisconnect(c)); conns.clear(); h.onError('offline'); },
  });
  return { drop:cid => { if (conns.delete(cid)) { link.send({op:'drop', to:cid}); h.onDisconnect(cid); } },
    send:(cid, data) => { if (conns.has(cid)) link.send({op:'data', to:cid, data}); },
    broadcast:data => { if (conns.size) link.send({op:'data', to:'*', data}); },
    close:() => link.close(), get via(){ return link.via; } };
}
function relayJoin(code, h){
  const link = relayLink(relayBase(), 'join', code, {
    onOpen:() => h.onOpen(), onError:e => h.onError(e), onMsg:m => { if (m.op === 'data') h.onMessage(m.data); }, onEnd:() => h.onClose() });
  return { send:data => link.send({op:'data', data}), close:() => link.close(), get via(){ return link.via; } };
}

/* A quick test a teacher can run before class: can this device reach the classroom server, and which way? */
async function timed(url, ms){ const c = new AbortController(), t = setTimeout(() => c.abort(), ms), t0 = performance.now();
  try { const r = await fetch(url, {cache:'no-store', signal:c.signal}); await r.json(); return r.ok ? Math.round(performance.now() - t0) : null; }
  catch (e) { return null; } finally { clearTimeout(t); } }
function wsEcho(url, ms){ return new Promise(done => { let s; try { s = new WebSocket(url); } catch (e) { return done(false); }
  const t = setTimeout(() => { try { s.close(); } catch (e) {} done(false); }, ms);
  s.onopen = () => s.send('{"hi":1}'); s.onmessage = () => { clearTimeout(t); s.close(); done(true); };
  s.onerror = s.onclose = () => { clearTimeout(t); done(false); }; }); }
SC.netCheck = async () => {
  const m = mode();
  if (m === 'local') return {mode:m, ok:true};
  if (m === 'peer') return new Promise(done => { if (typeof window.Peer !== 'function') return done({mode:m, ok:false});
    const p = new window.Peer(peerOpts()), t = setTimeout(() => { try { p.destroy(); } catch (e) {} done({mode:m, ok:false}); }, 8000);
    p.on('open', () => { clearTimeout(t); p.destroy(); done({mode:m, ok:true}); });
    p.on('error', () => { clearTimeout(t); try { p.destroy(); } catch (e) {} done({mode:m, ok:false}); }); });
  const base = relayBase(), ms = await timed(base + '/relay/hello', 8000);
  const ws = ms != null && typeof WebSocket === 'function' && await wsEcho(base.replace(/^http/, 'ws') + '/relay/ws?echo=1', 5000);
  return {mode:m, ok:ms != null, ms, ws, host:hostName(base)};
};

function localHost(code, h){
  const ch = new BroadcastChannel('sc-' + code), conns = new Set();
  ch.onmessage = e => { const m = e.data; if (!m || m.to !== 'host') return;
    if (m.kind === 'open') { conns.add(m.from); h.onConnect(m.from); ch.postMessage({to:m.from, from:'host', kind:'accept'}); }
    else if (m.kind === 'close') { conns.delete(m.from); h.onDisconnect(m.from); }
    else if (conns.has(m.from)) h.onMessage(m.from, m.data); };
  setTimeout(() => h.onOpen(), 50);
  return { drop:cid => { if (conns.delete(cid)) { ch.postMessage({to:cid, from:'host', kind:'close'}); h.onDisconnect(cid); } },
    send:(cid, data) => ch.postMessage({to:cid, from:'host', kind:'data', data}),
    broadcast:data => conns.forEach(cid => ch.postMessage({to:cid, from:'host', kind:'data', data})),
    close:() => { conns.forEach(cid => ch.postMessage({to:cid, from:'host', kind:'close'})); ch.close(); } };
}
function localJoin(code, h){
  const ch = new BroadcastChannel('sc-' + code), me = 'c' + Math.random().toString(36).slice(2,9);
  let open = false;
  ch.onmessage = e => { const m = e.data; if (!m || m.to !== me) return;
    if (m.kind === 'accept') { open = true; h.onOpen(); }
    else if (m.kind === 'close') { h.onClose(); }
    else if (m.kind === 'data') h.onMessage(m.data); };
  ch.postMessage({to:'host', from:me, kind:'open'});
  setTimeout(() => { if (!open) h.onError('notfound'); }, 2500);
  addEventListener('pagehide', () => ch.postMessage({to:'host', from:me, kind:'close'}));
  return { send:data => ch.postMessage({to:'host', from:me, kind:'data', data}),
    close:() => { ch.postMessage({to:'host', from:me, kind:'close'}); ch.close(); } };
}

function peerHost(code, h){
  const peer = new window.Peer(PREFIX + code, peerOpts()), conns = new Map();
  peer.on('open', () => h.onOpen());
  peer.on('error', e => h.onError(e.type === 'unavailable-id' ? 'taken' : e.type === 'network' || e.type === 'server-error' || e.type === 'socket-error' ? 'offline' : e.type));
  peer.on('disconnected', () => { try { peer.reconnect(); } catch (e) {} });
  peer.on('connection', conn => {
    conn.on('open', () => { conns.set(conn.connectionId, conn); h.onConnect(conn.connectionId); });
    conn.on('data', d => h.onMessage(conn.connectionId, d));
    const gone = () => { if (conns.delete(conn.connectionId)) h.onDisconnect(conn.connectionId); };
    conn.on('close', gone); conn.on('error', gone);
  });
  return { drop:cid => { const c = conns.get(cid); if (c && conns.delete(cid)) { try { c.close(); } catch (e) {} h.onDisconnect(cid); } },
    send:(cid, data) => { const c = conns.get(cid); if (c && c.open) c.send(data); },
    broadcast:data => conns.forEach(c => { if (c.open) c.send(data); }),
    close:() => { try { peer.destroy(); } catch (e) {} } };
}
function peerJoin(code, h){
  const peer = new window.Peer(peerOpts()); let conn = null, opened = false;
  peer.on('open', () => {
    conn = peer.connect(PREFIX + code, {reliable:true});
    conn.on('open', () => { opened = true; h.onOpen(); });
    conn.on('data', d => h.onMessage(d));
    conn.on('close', () => h.onClose());
    conn.on('error', () => h.onClose());
  });
  peer.on('error', e => h.onError(e.type === 'peer-unavailable' ? 'notfound' : e.type === 'network' || e.type === 'server-error' || e.type === 'socket-error' ? 'offline' : e.type));
  setTimeout(() => { if (!opened) h.onError('timeout'); }, 15000);
  return { send:data => { if (conn && conn.open) conn.send(data); }, close:() => { try { peer.destroy(); } catch (e) {} } };
}
SC.Net = {
  host: (code, h) => ({local:localHost, relay:relayHost, peer:peerHost})[mode()](code, h),
  join: (code, h) => ({local:localJoin, relay:relayJoin, peer:peerJoin})[mode()](code, h),
  errorText: e => ({taken:'That room code is already in use. Try hosting again.', notfound:'No game found with that code. Check the code and make sure the host has the lobby open.',
    full:'This game is full.', busy:'The classroom server is very busy. Try again in a minute.',
    offline: mode() === 'relay' ? `Could not reach the classroom server (${hostName(relayBase())}). If this page loads but joining fails, ask IT to allow that address.`
      : 'Could not reach the connection service. School networks often block it: see "For teachers" for a school-safe setup.',
    timeout:'Connecting took too long. Check the code and try again.'}[e] || `Connection problem (${e}). Try again.`),
};
})();

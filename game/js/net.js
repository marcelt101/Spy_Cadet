/* Networking, from Crater Crew. The host's browser is the server. Devices find each other through PeerJS,
   then talk directly over WebRTC. "?net=local" uses a BroadcastChannel instead, for testing
   several windows of one browser on one computer. */
(function () {
const SC = window.SC = window.SC || {};
const PREFIX = 'spy-cadet-v1-';
const ALPHA = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
SC.makeRoomCode = () => { let s = ''; for (let i=0;i<4;i++) s += ALPHA[Math.floor(Math.random()*ALPHA.length)]; return s; };
SC.cleanCode = c => String(c||'').toUpperCase().replace(/^SPY-?/,'').replace(/[^A-Z0-9]/g,'').slice(0,4);
const useLocal = () => /[?&]net=local\b/.test(location.search);
/* Optional self-hosted connection server, e.g. ?peerhost=192.168.1.20&peerport=9000 */
const peerOpts = () => { const q = new URLSearchParams(location.search), o = {debug:0};
  if (q.get('peerhost')) { o.host = q.get('peerhost'); o.port = +(q.get('peerport') || 9000); o.path = q.get('peerpath') || '/'; o.secure = q.get('peersecure') === '1'; }
  return o; };
SC.netAvailable = () => useLocal() || typeof window.Peer === 'function';

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
  host: (code, h) => useLocal() ? localHost(code, h) : peerHost(code, h),
  join: (code, h) => useLocal() ? localJoin(code, h) : peerJoin(code, h),
  errorText: e => ({taken:'That room code is already in use. Try hosting again.', notfound:'No game found with that code. Check the code and make sure the host has the lobby open.',
    offline:'Could not reach the connection service. Check that this device is online.', timeout:'Connecting took too long. Check the code and try again.'}[e] || `Connection problem (${e}). Try again.`),
};
})();

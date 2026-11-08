#!/usr/bin/env node
/* Spy Cadet classroom server: serves the game and relays team-game messages. No dependencies.

     node server/relay.js            # http://localhost:8080   (PORT=… to change)

   Why: school firewalls often block WebRTC (UDP) and the PeerJS service, so the direct connections Crater Crew used
   fail in class. This server carries every message over plain HTTPS on port 443, on the SAME address that serves the
   game: if a school can open the game, it can play it. Two ways to talk, chosen per device automatically:
     - WebSocket   /relay/ws?token=…         fast; used when the network allows it
     - long-poll   GET /relay/poll, POST /relay/send   ordinary web requests; works through strict filters and proxies
   The host's browser still runs the game rules; this server only passes messages between the host and the players.

   Sessions survive short drops: every message has a number and stays queued until the other side confirms it, so a
   device that loses Wi-Fi for a few seconds (or switches from WebSocket to long-poll) picks up where it left off. */
'use strict';
const http = require('http'), fs = require('fs'), path = require('path'), crypto = require('crypto');

const LIMITS = { rooms:2000, players:40, bodyBytes:512 * 1024, queue:2000, pollMs:20000, graceMs:30000 };
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.json':'application/json', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.svg':'image/svg+xml',
  '.woff2':'font/woff2', '.txt':'text/plain; charset=utf-8', '.md':'text/plain; charset=utf-8', '.ico':'image/x-icon',
  '.mp3':'audio/mpeg', '.ogg':'audio/ogg', '.webmanifest':'application/manifest+json' };

function createRelay(opts = {}){
  const root = path.resolve(opts.root || path.join(__dirname, '..', 'game'));
  const L = { ...LIMITS, ...(opts.limits || {}) };
  const rooms = new Map(), sessions = new Map();
  const now = () => Date.now();
  const roomOk = r => typeof r === 'string' && /^[A-Z0-9]{4,8}$/.test(r);

  /* ---------- sessions: one per device in a room ---------- */
  function newSession(role, room, cid){
    const s = { token:crypto.randomBytes(18).toString('base64url'), role, room, cid, out:[], seq:0, inSeq:0,
      ws:null, waiter:null, seen:now(), ended:false };
    sessions.set(s.token, s); return s;
  }
  function push(s, msg){
    if (!s || s.ended && msg.op !== 'close') return;
    msg.seq = ++s.seq; s.out.push(msg);
    if (s.out.length > L.queue) { endSession(s, 'overflow'); return; }
    if (s.ws) s.ws.sendJSON({ msgs:[msg] });
    flushWaiter(s);
  }
  function ack(s, n){ n = +n || 0; while (s.out.length && s.out[0].seq <= n) s.out.shift(); }
  function pending(s, after){ return s.out.filter(m => m.seq > after); }
  function flushWaiter(s, force){
    const w = s.waiter; if (!w) return;
    const msgs = pending(s, w.after);
    if (!msgs.length && !force) return;
    clearTimeout(w.timer); s.waiter = null;
    json(w.res, 200, { ack:s.inSeq, msgs });
  }
  function endSession(s, why){
    if (s.ended) return; s.ended = true;
    const room = rooms.get(s.room);
    if (room && s.role === 'host' && room.host === s) {
      rooms.delete(s.room);
      room.clients.forEach(c => { push(c, { op:'close' }); c.ended = true; c.closeAt = now() + 5000; });
    } else if (room && s.role === 'join' && room.clients.get(s.cid) === s) {
      room.clients.delete(s.cid);
      if (why !== 'dropped') push(room.host, { op:'disconnect', cid:s.cid });
    }
    s.closeAt = s.closeAt || now() + 5000; // keep a moment so a final "close" can still be collected
    if (why !== 'left' && why !== 'dropped') push(s, { op:'close' });
  }
  function forget(s){
    sessions.delete(s.token);
    if (s.waiter) { clearTimeout(s.waiter.timer); json(s.waiter.res, 410, { error:'gone' }); s.waiter = null; }
    if (s.ws) { try { s.ws.close(); } catch (e) {} s.ws = null; }
  }
  const sweep = setInterval(() => {
    const t = now();
    sessions.forEach(s => {
      if (s.ended) { if (t > s.closeAt) forget(s); return; }
      if (!s.ws && !s.waiter && t - s.seen > L.graceMs) { endSession(s, 'timeout'); }
    });
  }, 2000);
  sweep.unref && sweep.unref();

  /* ---------- what a device can say ---------- */
  function receive(s, body){
    s.seen = now();
    if (body && body.ack != null) ack(s, body.ack);
    const msgs = Array.isArray(body && body.msgs) ? body.msgs : [];
    for (const m of msgs) {
      if (!m || typeof m !== 'object' || !(m.cseq > s.inSeq)) continue; // already handled (a resend)
      s.inSeq = m.cseq;
      if (s.ended) continue;
      const room = rooms.get(s.room); if (!room) continue;
      if (m.op === 'leave') { endSession(s, 'left'); continue; }
      if (s.role === 'join') { if (m.op === 'data') push(room.host, { op:'data', from:s.cid, data:m.data }); continue; }
      if (m.op === 'data') {
        if (m.to === '*') room.clients.forEach(c => push(c, { op:'data', data:m.data }));
        else push(room.clients.get(m.to), { op:'data', data:m.data });
      } else if (m.op === 'drop') {
        const c = room.clients.get(m.to); if (c) { push(c, { op:'close' }); endSession(c, 'dropped'); }
      }
    }
    return s.inSeq;
  }
  function open(body){
    const role = body && body.role, room = String(body && body.room || '').toUpperCase();
    if (!roomOk(room)) return [400, { error:'badroom' }];
    if (role === 'host') {
      const old = rooms.get(room);
      if (old && !old.host.ended) return [409, { error:'taken' }];
      if (rooms.size >= L.rooms) return [503, { error:'busy' }];
      const s = newSession('host', room); rooms.set(room, { host:s, clients:new Map(), n:0 });
      return [200, { token:s.token }];
    }
    if (role === 'join') {
      const r = rooms.get(room); if (!r) return [404, { error:'notfound' }];
      if (r.clients.size >= L.players) return [403, { error:'full' }];
      const cid = 'c' + (++r.n) + crypto.randomBytes(3).toString('hex'), s = newSession('join', room, cid);
      r.clients.set(cid, s); push(r.host, { op:'connect', cid });
      return [200, { token:s.token, cid }];
    }
    return [400, { error:'badrole' }];
  }

  /* ---------- HTTP ---------- */
  function json(res, code, obj){
    if (res.writableEnded) return;
    const b = JSON.stringify(obj);
    res.writeHead(code, { 'content-type':'application/json', 'cache-control':'no-store', 'access-control-allow-origin':'*',
      'content-length':Buffer.byteLength(b) });
    res.end(b);
  }
  function readBody(req, cb){
    let size = 0; const parts = [];
    req.on('data', c => { size += c.length; if (size > L.bodyBytes) { req.destroy(); return; } parts.push(c); });
    req.on('end', () => { let b = null; try { b = JSON.parse(Buffer.concat(parts).toString('utf8') || 'null'); } catch (e) {} cb(b); });
  }
  function relayHttp(req, res, u){
    const route = u.pathname.slice('/relay/'.length);
    if (req.method === 'OPTIONS') { res.writeHead(204, { 'access-control-allow-origin':'*', 'access-control-allow-methods':'GET, POST',
      'access-control-allow-headers':'content-type', 'access-control-max-age':'86400' }); return res.end(); }
    if (route === 'hello') return json(res, 200, { ok:true, app:'spy-cadet-relay', rooms:rooms.size });
    if (route === 'open' && req.method === 'POST') return readBody(req, b => { const [c, o] = open(b); json(res, c, o); });
    const s = sessions.get(u.searchParams.get('token') || '');
    if (!s) return json(res, 410, { error:'gone' });
    if (route === 'send' && req.method === 'POST') return readBody(req, b => json(res, 200, { ack:receive(s, b) }));
    if (route === 'poll' && req.method === 'GET') {
      s.seen = now();
      const after = +u.searchParams.get('ack') || 0; ack(s, after);
      if (s.waiter) flushWaiter(s, true);  // only one poll waits at a time; answer the older one
      s.waiter = { res, after, timer:setTimeout(() => { if (s.waiter && s.waiter.res === res) { s.waiter = null; s.seen = now(); json(res, 200, { ack:s.inSeq, msgs:[] }); } }, L.pollMs) };
      res.on('close', () => { if (s.waiter && s.waiter.res === res) { clearTimeout(s.waiter.timer); s.waiter = null; s.seen = now(); } });
      flushWaiter(s);
      return;
    }
    json(res, 404, { error:'nope' });
  }
  function serveFile(req, res, u){
    let p; try { p = decodeURIComponent(u.pathname); } catch (e) { res.writeHead(400); return res.end(); }
    if (p === '/js/config.js') { // the game finds this server at its own address
      res.writeHead(200, { 'content-type':TYPES['.js'], 'cache-control':'no-cache' });
      return res.end('/* written by server/relay.js */\nwindow.SC = window.SC || {};\nwindow.SC.RELAY_URL = location.origin;\n');
    }
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(root, path.normalize(p));
    if (!file.startsWith(root + path.sep)) { res.writeHead(403); return res.end(); }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) {
        if (!err && st.isDirectory()) { res.writeHead(301, { location:p + '/' }); return res.end(); }
        res.writeHead(404, { 'content-type':'text/plain' }); return res.end('Not found');
      }
      res.writeHead(200, { 'content-type':TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
        'content-length':st.size, 'cache-control':'no-cache' });
      if (req.method === 'HEAD') return res.end();
      fs.createReadStream(file).pipe(res);
    });
  }
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    if (u.pathname.startsWith('/relay/')) return relayHttp(req, res, u);
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
    serveFile(req, res, u);
  });

  /* ---------- WebSocket (RFC 6455, text frames only) ---------- */
  server.on('upgrade', (req, sock) => {
    const u = new URL(req.url, 'http://x'), key = req.headers['sec-websocket-key'];
    const echo = u.pathname === '/relay/ws' && u.searchParams.get('echo') === '1';
    const s = sessions.get(u.searchParams.get('token') || '');
    if (u.pathname !== '/relay/ws' || !key || (!s && !echo) || (s && s.ended)) { sock.end('HTTP/1.1 410 Gone\r\n\r\n'); return; }
    const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
    sock.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ' + accept + '\r\n\r\n');
    sock.setNoDelay(true);
    const ws = wrapSocket(sock, text => {
      let b = null; try { b = JSON.parse(text); } catch (e) { return; }
      if (echo) { ws.sendJSON(b); return; }
      if (s.ws !== ws) return;
      ws.sendJSON({ ack:receive(s, b) }); // every frame gets an answer, so the device knows the line is alive
    }, () => { if (s && s.ws === ws) { s.ws = null; s.seen = now(); } });
    if (echo) return;
    if (s.ws) { try { s.ws.close(); } catch (e) {} }
    s.ws = ws; s.seen = now();
    if (s.waiter) flushWaiter(s, true);
    ws.sendJSON({ ack:s.inSeq, msgs:s.out }); // everything not yet confirmed
  });
  function wrapSocket(sock, onText, onClose){
    let buf = Buffer.alloc(0), frag = [], closed = false, gone = false;
    const frame = (op, payload) => {
      const n = payload.length; let h;
      if (n < 126) { h = Buffer.from([0x80 | op, n]); }
      else if (n < 65536) { h = Buffer.alloc(4); h[0] = 0x80 | op; h[1] = 126; h.writeUInt16BE(n, 2); }
      else { h = Buffer.alloc(10); h[0] = 0x80 | op; h[1] = 127; h.writeBigUInt64BE(BigInt(n), 2); }
      if (!closed) sock.write(Buffer.concat([h, payload]));
    };
    const ws = {
      sendJSON: o => frame(1, Buffer.from(JSON.stringify(o), 'utf8')),
      close: () => { if (closed) return; frame(8, Buffer.alloc(0)); closed = true; sock.end(); },
    };
    const keep = setInterval(() => frame(9, Buffer.alloc(0)), 25000); // pings stop proxies dropping a quiet socket
    const done = () => { if (gone) return; gone = true; closed = true; clearInterval(keep); onClose(); };
    sock.on('data', d => {
      buf = Buffer.concat([buf, d]);
      while (buf.length >= 2) {
        const fin = buf[0] & 0x80, op = buf[0] & 0x0f, masked = buf[1] & 0x80; let n = buf[1] & 0x7f, off = 2;
        if (n === 126) { if (buf.length < 4) return; n = buf.readUInt16BE(2); off = 4; }
        else if (n === 127) { if (buf.length < 10) return; n = Number(buf.readBigUInt64BE(2)); off = 10; }
        if (n > L.bodyBytes) { sock.destroy(); return; }
        const mo = off; if (masked) off += 4;
        if (buf.length < off + n) return;
        let p = buf.subarray(off, off + n);
        if (masked) { const m = buf.subarray(mo, mo + 4); p = Buffer.from(p); for (let i = 0; i < p.length; i++) p[i] ^= m[i & 3]; }
        buf = buf.subarray(off + n);
        if (op === 8) { ws.close(); return; }
        if (op === 9) { frame(10, p); continue; }
        if (op === 10) continue;
        if (op === 1 || op === 0) { frag.push(p); if (fin) { const t = Buffer.concat(frag).toString('utf8'); frag = []; onText(t); } }
      }
    });
    sock.on('close', done); sock.on('error', () => { try { sock.destroy(); } catch (e) {} });
    return ws;
  }

  server.stats = () => ({ rooms:rooms.size, sessions:sessions.size });
  server.on('close', () => clearInterval(sweep));
  return server;
}

module.exports = { createRelay };

if (require.main === module) {
  const port = +process.env.PORT || 8080, host = process.env.HOST || '0.0.0.0';
  createRelay({ root:process.env.GAME_DIR }).listen(port, host, () => {
    const ips = Object.values(require('os').networkInterfaces()).flat().filter(i => i && i.family === 'IPv4' && !i.internal).map(i => i.address);
    console.log(`Spy Cadet server on port ${port}`);
    console.log(`  this computer:  http://localhost:${port}/`);
    ips.forEach(ip => console.log(`  same network:   http://${ip}:${port}/`));
  });
}

/* Tests for the school-safe classroom server (server/relay.js) and the game's relay client (game/js/net.js).
     node tests/relay-test.js
   Starts a real server on a free port, then drives the game's own net.js in Node: a host and several players,
   over WebSocket and over long-poll, including a dropped line, kicking a player and the host leaving. */
'use strict';
const path = require('path'), fs = require('fs'), vm = require('vm');
const { createRelay } = require('../server/relay.js');
let pass = 0, fail = 0;
const ok = (c, msg) => { if (c) pass++; else { fail++; console.log('FAIL', msg); } };
const eq = (a, b, msg) => ok(JSON.stringify(a) === JSON.stringify(b), `${msg}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`);
const wait = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, ms = 4000, msg = 'condition'){ const t = Date.now(); while (Date.now() - t < ms) { if (fn()) return true; await wait(20); } ok(false, 'timed out waiting for ' + msg); return false; }

(async () => {
  const server = createRelay({ limits:{ pollMs:600, graceMs:1500, players:5 } });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const post = (p, b) => fetch(base + p, { method:'POST', body:JSON.stringify(b), headers:{ 'content-type':'text/plain' } }).then(async r => ({ s:r.status, j:await r.json() }));
  const get = p => fetch(base + p).then(async r => ({ s:r.status, j:await r.json().catch(() => null) }));

  /* ---------- the raw protocol ---------- */
  eq((await get('/relay/hello')).j.ok, true, 'hello answers');
  eq((await post('/relay/open', { role:'join', room:'ZZZZ' })).j.error, 'notfound', 'joining a missing room');
  eq((await post('/relay/open', { role:'host', room:'../x' })).s, 400, 'bad room codes are refused');
  const H = (await post('/relay/open', { role:'host', room:'ABCD' })).j;
  ok(H.token, 'host gets a token');
  eq((await post('/relay/open', { role:'host', room:'ABCD' })).j.error, 'taken', 'a room code cannot be hosted twice');
  const P = (await post('/relay/open', { role:'join', room:'abcd' })).j;
  ok(P.token && P.cid, 'player gets a token and an id (codes are case-blind)');
  let r = await get(`/relay/poll?token=${H.token}&ack=0`);
  eq(r.j.msgs.map(m => m.op), ['connect'], 'host hears the player connect');
  await post(`/relay/send?token=${P.token}`, { msgs:[{ cseq:1, op:'data', data:{ hi:1 } }, { cseq:1, op:'data', data:{ dup:1 } }] });
  r = await get(`/relay/poll?token=${H.token}&ack=1`);
  eq(r.j.msgs.map(m => m.data), [{ hi:1 }], 'player message reaches the host once (resends are ignored)');
  const t0 = Date.now(); r = await get(`/relay/poll?token=${P.token}&ack=0`);
  ok(Date.now() - t0 >= 500 && r.j.msgs.length === 0, 'an empty poll waits, then answers');
  const late = get(`/relay/poll?token=${P.token}&ack=0`);
  await wait(50); await post(`/relay/send?token=${H.token}`, { msgs:[{ cseq:1, op:'data', to:'*', data:{ all:1 } }] });
  r = await late; eq(r.j.msgs.map(m => m.data), [{ all:1 }], 'a waiting poll gets the host broadcast at once');
  r = await get(`/relay/poll?token=${P.token}&ack=0`);
  eq(r.j.msgs.length, 1, 'unconfirmed messages are sent again');

  /* WebSocket on the same session, then a dropped line, then long-poll picks up */
  const ws = new WebSocket(base.replace('http', 'ws') + `/relay/ws?token=${P.token}`), got = [];
  ws.onmessage = e => got.push(JSON.parse(e.data));
  await until(() => got.length, 2000, 'websocket first frame');
  eq(got[0].msgs.map(m => m.data), [{ all:1 }], 'websocket resumes with what is still unconfirmed');
  ws.send(JSON.stringify({ ack:1, msgs:[{ cseq:2, op:'data', data:{ viaWs:1 } }] }));
  await until(() => got.some(b => b.ack === 2), 2000, 'websocket ack');
  r = await get(`/relay/poll?token=${H.token}&ack=2`); eq(r.j.msgs.map(m => m.data), [{ viaWs:1 }], 'websocket message reaches the host');
  ws.close(); await wait(100);
  await post(`/relay/send?token=${H.token}`, { msgs:[{ cseq:2, op:'data', to:P.cid, data:{ afterDrop:1 } }] });
  r = await get(`/relay/poll?token=${P.token}&ack=1`); eq(r.j.msgs.map(m => m.data), [{ afterDrop:1 }], 'after the websocket drops, long-poll gets the waiting message');
  eq(await new Promise(done => { const e = new WebSocket(base.replace('http', 'ws') + '/relay/ws?echo=1'); e.onopen = () => e.send('{"x":1}'); e.onmessage = m => { e.close(); done(JSON.parse(m.data)); }; e.onerror = () => done(null); }), { x:1 }, 'network check echo');

  /* a device that goes quiet is let go; when the host goes, players are told */
  await wait(4000);
  r = await get(`/relay/poll?token=${H.token}&ack=0`); ok(r.s === 410 || (r.j.msgs || []).some(m => m.op === 'close'), 'a host that stopped polling is let go');
  r = await get(`/relay/poll?token=${P.token}&ack=2`);
  ok(r.s === 410 || (r.j.msgs || []).some(m => m.op === 'close'), 'players learn the room closed');
  ok((await post('/relay/open', { role:'host', room:'ABCD' })).j.token, 'the code is free again');

  /* static files */
  const page = await fetch(base + '/'); ok(page.ok && (await page.text()).includes('Spy Cadet'), 'serves the game');
  const cfg = await (await fetch(base + '/js/config.js')).text(); ok(cfg.includes('location.origin'), 'config.js points the game at this server');
  ok(!(await fetch(base + '/%2e%2e/server/relay.js')).ok, 'no files outside game/');
  eq((await fetch(base + '/js/../../README.md')).status === 200, false, 'no climbing out of game/');

  /* ---------- the game's own client: game/js/net.js ---------- */
  const sandbox = { console, setTimeout, clearTimeout, setInterval, clearInterval, fetch, WebSocket, URL, URLSearchParams, AbortController,
    performance, JSON, Promise, navigator:{}, location:{ search:'?relay=' + base, origin:base }, addEventListener(){} };
  sandbox.window = sandbox; vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../game/js/net.js'), 'utf8'), sandbox);
  const SC = sandbox.SC;
  eq(SC.netMode(), 'relay', 'a relay address in the link selects the relay');
  const chk = await SC.netCheck(); ok(chk.ok && chk.ws, 'network check: server and websocket reachable');

  for (const via of ['websocket', 'poll']) {
    sandbox.location.search = '?relay=' + base + (via === 'poll' ? '&via=poll' : '');
    const code = via === 'poll' ? 'POLL' : 'WSOK', host = { conns:[], msgs:[], gone:[], open:false };
    const hn = SC.Net.host(code, { onOpen:() => host.open = true, onError:e => host.err = e, onConnect:c => host.conns.push(c),
      onDisconnect:c => host.gone.push(c), onMessage:(c, m) => { host.msgs.push([c, m]); if (m.ping != null) hn.send(c, { pong:m.ping }); } });
    await until(() => host.open, 3000, via + ' host open');
    const players = [0, 1, 2].map(i => { const p = { i, msgs:[], open:false, closed:false };
      p.net = SC.Net.join(code, { onOpen:() => { p.open = true; p.net.send({ hello:i }); }, onMessage:m => p.msgs.push(m), onClose:() => p.closed = true, onError:e => p.err = e });
      return p; });
    await until(() => players.every(p => p.open) && host.msgs.length === 3, 6000, via + ' three players say hello');
    eq(host.msgs.map(([, m]) => m.hello).sort(), [0, 1, 2], `${via}: every hello reaches the host`);
    hn.broadcast({ start:'m1' });
    await until(() => players.every(p => p.msgs.some(m => m.start)), 4000, via + ' broadcast');
    ok(players.every(p => p.msgs.some(m => m.start === 'm1')), `${via}: the broadcast reaches every player`);
    for (let k = 0; k < 20; k++) players[1].net.send({ ping:k });
    await until(() => players[1].msgs.filter(m => m.pong != null).length === 20, 6000, via + ' 20 round trips');
    eq(players[1].msgs.filter(m => m.pong != null).map(m => m.pong), [...Array(20).keys()], `${via}: 20 messages each way, in order`);
    if (via === 'websocket') ok(hn.via === 'websocket', 'the host uses a websocket when it can');
    else ok(hn.via === 'long-poll', '?via=poll uses the backup');
    const cid2 = host.msgs.find(([, m]) => m.hello === 2)[0];
    hn.drop(cid2); await until(() => players[2].closed, 4000, via + ' kicked player closes');
    ok(players[2].closed, `${via}: a kicked player is told`);
    players[0].net.close(); await until(() => host.gone.length >= 2, 4000, via + ' leaver noticed');
    ok(host.gone.length === 2, `${via}: the host hears a player leave`);
    hn.close(); await until(() => players[1].closed, 4000, via + ' host left');
    ok(players[1].closed, `${via}: players hear the host leave`);
  }
  sandbox.location.search = '?relay=' + base;
  const nf = await new Promise(done => SC.Net.join('NONE', { onOpen:() => done('open'), onError:e => done(e), onMessage(){}, onClose(){} }));
  eq(nf, 'notfound', 'joining a code nobody hosts');

  server.close(); server.closeAllConnections && server.closeAllConnections();
  console.log(`relay: ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL', e); process.exit(1); });

/* Run with: node tests/run-tests.js
   Unit tests for the code book cipher and the mission rules, plus a robot that plays every mission to the end. */
global.window = global;
const fs = require('fs'), path = require('path');
for (const f of ['codebook', 'content', 'engine']) eval(fs.readFileSync(path.join(__dirname, '../game/js', f + '.js'), 'utf8'));
const SC = window.SC, C = SC.Code, E = SC.Engine;
let pass = 0, fail = 0;
const ok = (cond, name) => { if (cond) pass++; else { fail++; console.log('FAIL', name); } };
const eq = (a, b, name) => ok(JSON.stringify(a) === JSON.stringify(b), `${name}: got ${JSON.stringify(a)}, want ${JSON.stringify(b)}`);

/* ---------- cipher ---------- */
eq(C.add('47250', '31819'), '78069', 'add without carrying (example from the design paper)');
eq(C.sub('78069', '31819'), '47250', 'subtract without borrowing');
eq(C.sub('00000', '99999'), '11111', 'every digit wraps');
eq(C.digitMath(8, 3), '8 − 3 = 5', 'digit math');
eq(C.digitMath(2, 7), '2 − 7: think 12 − 7 = 5', 'digit math with wrap');
ok(C.div3('47250') && !C.div3('47251'), 'divides by 3');
for (let i = 0; i < 2000; i++) { const a = String(Math.floor(Math.random() * 1e5)).padStart(5, '0'), b = String(Math.floor(Math.random() * 1e5)).padStart(5, '0');
  if (C.sub(C.add(a, b), b) !== a) { ok(false, 'add then sub gives back ' + a); break; } }
const book = E.book(), groups = Object.values(book);
eq(new Set(groups).size, groups.length, 'every code group is different');
ok(groups.every(g => g.length === 5 && C.div3(g) && g[0] !== '0'), 'every code group has 5 digits, divides by 3 and does not start with 0');
eq(Object.keys(book).length, SC.ALL_WORDS.length, 'one group per word');
ok(new Set(SC.ALL_WORDS).size === SC.ALL_WORDS.length, 'no word is listed twice');
eq(JSON.stringify(E.book()), JSON.stringify(C.makeBook(SC.ALL_WORDS, SC.hashSeed('jn25-1942'))), 'the code book is the same every time');
const add = C.makeAdditives(50, 7), enc = C.encrypt(['FROM', 'TANKER', 'ARRIVES'], book, add, 45);
eq(C.decrypt(enc.map(g => g.cipher), add, 45).map(g => C.lookup(g, book)), ['FROM', 'TANKER', 'ARRIVES'], 'encrypt then decrypt, with the additive list wrapping');
const chk = C.check('78069', '31819', '47350');
ok(!chk.ok && chk.at === 2 && chk.want === '47250', 'check finds the first wrong digit');
ok(C.check('78069', '31819', '47250').ok, 'check accepts the right answer');
ok(C.hints({cipher:'78069', add:'31819', typed:'4', tries:3}).includes('Digit 2'), 'hint gives the math for the next digit');

/* ---------- content ---------- */
SC.CAMPAIGNS.forEach(c => c.missions.forEach(m => {
  Object.values(m.messages).forEach(msg => msg.words.forEach(w => ok(book[w], `${m.id}: "${w}" is in the code book`)));
  m.phases.forEach(ph => {
    if (ph.k === 'decode') ph.keys.forEach(k => ok(m.messages[k], `${m.id}: message ${k} exists`));
    if (ph.k === 'vote') eq(ph.opts.filter(o => o.ok).length, 1, `${m.id}/${ph.id}: exactly one right answer`);
    if (ph.k === 'vote') ok(ph.opts.every(o => o.why), `${m.id}/${ph.id}: every answer has an explanation`);
  });
  Object.entries(m.targets || {}).forEach(([w, t]) => {
    ok(t.opts.includes(w), `${m.id}: the answer ${w} is one of the choices`);
    ok(t.opts.every(o => book[o]), `${m.id}: every choice for ${w} is a code book word`);
    ok(t.opts.filter(o => o !== w).every(o => t.why[o]), `${m.id}: every wrong choice for ${w} is explained`);
    ok(Object.values(m.messages).some(msg => msg.words.includes(w)), `${m.id}: ${w} appears in a message`);
  });
  ok(SC.PEOPLE[m.history.person], `${m.id}: history card person exists`);
  (m.news || []).forEach(n => ok(n.t.split(' ').length <= 12, `${m.id}: headline under 12 words: ${n.t}`));
}));

/* ---------- mission rules ---------- */
const st0 = E.newState('m2', 1, {n:1, level:'codebreaker'}), B0 = E.build('m2', 1, 1);
eq(JSON.stringify(E.build('m2', 1, 1).intercepts), JSON.stringify(B0.intercepts), 'the same seed builds the same intercepts');
ok(E.unknownAt('m2').has('PORT MORESBY') && !E.unknownAt('m2').has('TRUK'), 'words found in earlier missions are known');
E.take(st0, B0, 'a'); ok(B0.byId[st0.assign.a].key, 'key messages are handed out first');
eq(E.file(st0, B0, 'a', 'k2'), [], 'a message with an unknown word cannot be filed');
eq(E.recover(st0, B0, 'a', 'PORT MORESBY', 'HAWAII')[0].t, 'wrongGuess', 'a wrong guess is refused with a reason');
eq(E.recover(st0, B0, 'a', 'PORT MORESBY', 'PORT MORESBY')[0].t, 'recovered', 'the right guess is recovered');
const vs = E.newState('m1', 1); vs.phase = 1;
E.vote(vs, 'a', 1); E.vote(vs, 'b', 0); E.vote(vs, 'c', 1);
eq(E.tally(vs).best, 1, 'the most popular answer wins');
const wrong = E.closeVote(vs); ok(!wrong[0].ok && vs.round === 1 && !Object.keys(vs.votes).length, 'a wrong team answer clears the votes for another round');
E.vote(vs, 'a', 2); E.vote(vs, 'b', 0); eq(E.tally(vs).best, 2, 'a tie goes to the earliest vote');
const ts = E.newState('m2', 1, {level:'codebreaker'}); E.tick(ts, 1000); ok(ts.late, 'the clock runs out');
ok(!E.newState('m2', 1, {level:'recruit'}).limit, 'recruits have no clock');
eq(E.stars({hints:0, slips:1}, false), 3, '3 stars'); eq(E.stars({hints:1, slips:2}, false), 2, '2 stars'); eq(E.stars({hints:0, slips:0}, true), 2, 'late caps stars');

/* ---------- robot players: every mission must be playable to the end, alone and in teams ---------- */
SC.CAMPAIGNS.forEach(c => c.missions.forEach(m => [1, 2, 7, 32].forEach(n => {
  const seed = 1000 + n, B = E.build(m.id, seed, n), st = E.newState(m.id, seed, {n}), pids = [...Array(n)].map((_, i) => 'p' + i);
  let steps = 0, events = 0;
  while (!st.done && steps++ < 5000) {
    const ph = E.phase(st);
    if (ph.k === 'vote') { pids.forEach((p, i) => E.vote(st, p, i % ph.opts.length)); events += E.closeVote(st).length; continue; }
    for (const p of pids) {
      E.take(st, B, p); const iid = st.assign[p]; if (!iid) continue;
      const x = B.byId[iid];
      ok(C.decrypt(x.groups.map(g => g.cipher), B.additives, x.start).every((g, k) => C.lookup(g, book) === x.words[k]), `${m.id}: intercept ${iid} decodes`);
      E.missing(st, B, iid).forEach(w => E.recover(st, B, p, w, w));
      events += E.file(st, B, p, iid).length;
      if (st.done || E.phase(st).k !== 'decode') break;
    }
  }
  ok(st.done === 'win', `${m.id} with ${n} player(s) can be finished (got ${st.done} after ${steps} steps)`);
  if (n === 32) ok(B.intercepts.length >= 32, `${m.id}: enough messages for 32 players`);
})));

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);

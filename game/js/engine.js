/* Mission rules. One mission is a list of phases: "decode" (read the key messages) and "vote" (the team decides).
   Every device builds the same intercepts from the mission id, a seed and the player count, so only the small
   shared state travels over the network. The host (or the solo player's own device) applies every action.
   Pure functions, no screen code, so the tests and the robot playtesters can use it. */
(function () {
const SC = window.SC = window.SC || {};
const C = SC.Code;

let bookCache = null;
const ADDITIVES = 400;

const E = SC.Engine = {
  /* The codebook stays the same in every game, like the real one: players can start to remember groups. */
  book(){ return bookCache || (bookCache = C.makeBook(SC.ALL_WORDS, SC.hashSeed('jn25-1942'))); },
  find(mid){ for (const c of SC.CAMPAIGNS) { const i = c.missions.findIndex(m => m.id === mid); if (i >= 0) return {c, m:c.missions[i], i}; } return null; },
  /* Target words of this mission and later ones are still unknown; earlier missions' finds are in the book. */
  unknownAt(mid){
    const {c, i} = E.find(mid), out = new Set();
    c.missions.slice(i).forEach(m => Object.keys(m.targets || {}).forEach(w => out.add(w)));
    return out;
  },
  filler(r){
    const F = SC.FILLER, pat = SC.pick(r, F.patterns);
    return pat.map(w => w[0] === '$' ? SC.pick(r, F[{$sender:'senders', $base:'bases', $weather:'weather', $day:'day'}[w]]) : w);
  },
  /* All intercepts of one mission run. Key messages come from the mission; filler fills the pool for big teams. */
  build(mid, seed, n = 1){
    const {m} = E.find(mid), r = SC.rng(seed ^ SC.hashSeed(mid)), book = E.book();
    const additives = C.makeAdditives(ADDITIVES, seed ^ SC.hashSeed(mid + '/add'));
    const intercepts = [], unknown = E.unknownAt(mid);
    let fid = 0;
    const add = (id, key, phase, words) => {
      const start = Math.floor(r() * (ADDITIVES - 10));
      intercepts.push({id, key, phase, words, start, groups:C.encrypt(words, book, additives, start),
        time:`${String(Math.floor(r() * 24)).padStart(2, '0')}${String(Math.floor(r() * 60)).padStart(2, '0')}`,
        freq:(4 + Math.floor(r() * 12)) + '.' + Math.floor(r() * 10) + ' MHz'});
    };
    m.phases.forEach((ph, pi) => {
      if (ph.k !== 'decode') return;
      ph.keys.forEach(k => add(k, true, pi, m.messages[k].words));
      const nf = n > 1 ? Math.max(ph.filler, n * 2 - ph.keys.length) : ph.filler;
      for (let k = 0; k < nf; k++) add('f' + (fid++), false, pi, E.filler(r));
    });
    return {mid, seed, n, book, additives, intercepts, unknown, byId:Object.fromEntries(intercepts.map(x => [x.id, x]))};
  },
  limitFor(m, level){ return !SC.LEVELS[level].clock ? 0 : (m.limit || {})[level === 'expert' ? 'expert' : 'codebreaker'] || 0; },
  newState(mid, seed, {n = 1, level = 'codebreaker'} = {}){
    const {m} = E.find(mid);
    return {mid, seed, n, level, phase:0, t:0, limit:E.limitFor(m, level), assign:{}, taken:{}, filed:{}, recovered:{}, votes:{}, voteOrder:[],
      round:0, wrongVotes:0, fired:{}, done:null, late:false, last:null};
  },
  phase(st){ return E.find(st.mid).m.phases[st.phase] || null; },
  /* Which words of a message the player still needs to work out. */
  missing(st, B, iid){ const x = B.byId[iid]; return x.words.filter(w => B.unknown.has(w) && !st.recovered[w]); },
  known(st, B, w){ return !B.unknown.has(w) || !!st.recovered[w]; },

  /* ---------- actions (applied by the host). Each returns a list of events for the screens. ---------- */
  take(st, B, pid){
    const cur = st.assign[pid]; if (cur && !st.filed[cur]) return [];
    const ph = st.phase, pool = B.intercepts.filter(x => x.phase === ph && !st.filed[x.id]);
    const free = x => !(st.taken[x.id] || []).length;
    const pick = pool.find(x => x.key && free(x)) || pool.find(x => !x.key && free(x)) || pool.find(x => x.key) || null;
    if (!pick) { delete st.assign[pid]; return [{t:'nothing', pid}]; }
    st.assign[pid] = pick.id; (st.taken[pick.id] = st.taken[pick.id] || []).push(pid);
    return [{t:'assigned', pid, iid:pick.id}];
  },
  recover(st, B, pid, word, guess){
    if (!B.unknown.has(word)) return [];
    if (st.recovered[word]) return [{t:'recovered', pid:st.recovered[word], word, again:true}];
    const tg = E.find(st.mid).m.targets[word];
    if (guess !== word) return [{t:'wrongGuess', pid, word, guess, why:(tg.why || {})[guess] || SC.SAY.wrongTarget}];
    st.recovered[word] = pid;
    return [{t:'recovered', pid, word}];
  },
  file(st, B, pid, iid){
    const x = B.byId[iid]; if (!x || st.filed[iid] || st.done) return [];
    if (E.missing(st, B, iid).length) return [];
    st.filed[iid] = pid;
    Object.keys(st.assign).forEach(p => { if (st.assign[p] === iid) delete st.assign[p]; });
    const msg = x.key ? E.find(st.mid).m.messages[iid] : null;
    const ev = [{t:'filed', pid, iid, key:x.key, fact:msg && msg.fact || null}];
    return ev.concat(E.advance(st, B));
  },
  advance(st, B){
    const ph = E.phase(st); if (!ph || ph.k !== 'decode') return [];
    const keysLeft = B.intercepts.filter(x => x.phase === st.phase && x.key && !st.filed[x.id]);
    return keysLeft.length ? [] : E.nextPhase(st);
  },
  nextPhase(st){
    st.phase++; st.votes = {}; st.voteOrder = []; st.round = 0; st.assign = {};
    const {m} = E.find(st.mid), ev = [{t:'phase', i:st.phase}].concat(E.newsOn(st, 'phase:' + st.phase));
    if (st.phase >= m.phases.length) { st.done = st.late ? 'late' : 'win'; ev.push({t:'done', result:st.done}, ...E.newsOn(st, st.done)); }
    return ev;
  },
  vote(st, pid, opt){
    const ph = E.phase(st); if (!ph || ph.k !== 'vote' || !ph.opts[opt]) return [];
    if (st.votes[pid] == null) st.voteOrder.push(pid);
    st.votes[pid] = opt; return [{t:'votes', votes:{...st.votes}}];
  },
  /* Count the votes. The most popular answer wins; a tie goes to the answer that got its first vote earliest. */
  tally(st){
    const ph = E.phase(st), count = ph.opts.map(() => 0); Object.values(st.votes).forEach(o => count[o]++);
    const first = o => st.voteOrder.findIndex(p => st.votes[p] === o);
    let best = -1; count.forEach((c, o) => { if (c && (best < 0 || c > count[best] || (c === count[best] && first(o) < first(best)))) best = o; });
    return {count, best};
  },
  closeVote(st){
    const ph = E.phase(st); if (!ph || ph.k !== 'vote') return [];
    const {count, best} = E.tally(st); if (best < 0) return [];
    const o = ph.opts[best], ev = [{t:'voteResult', id:ph.id, opt:best, ok:!!o.ok, why:o.why, count, round:st.round}];
    if (o.ok) return ev.concat(E.nextPhase(st));
    st.votes = {}; st.voteOrder = []; st.round++; st.wrongVotes++; return ev;
  },
  tick(st, dt){
    if (st.done) return [];
    st.t += dt; const ev = [], {m} = E.find(st.mid);
    (m.news || []).forEach((n, i) => { if (n.at != null && st.t >= n.at && !st.fired[i]) { st.fired[i] = 1; ev.push({t:'news', i, text:n.t, icon:n.icon}); } });
    if (st.limit && !st.late && st.t >= st.limit) { st.late = true; ev.push({t:'late'}); }
    return ev;
  },
  newsOn(st, key){ const {m} = E.find(st.mid), ev = [];
    (m.news || []).forEach((n, i) => { if (n.on === key && !st.fired[i]) { st.fired[i] = 1; ev.push({t:'news', i, text:n.t, icon:n.icon}); } }); return ev; },

  /* The in-game date and time on the wall clock. */
  clock(st){ const {m} = E.find(st.mid), d = new Date(m.clockStart + ':00Z'); d.setUTCMinutes(d.getUTCMinutes() + Math.floor(st.t * (m.rate || 4))); return d; },
  /* Stars for one player: 3 with no hints and at most one slip, 2 with a few, 1 for finishing. A late finish gives at most 2. */
  stars(stats, late){ const s = stats.hints === 0 && stats.slips <= 1 ? 3 : stats.hints + stats.slips <= 5 ? 2 : 1; return late ? Math.min(2, s) : s; },
};
if (typeof module !== 'undefined') module.exports = SC;
})();

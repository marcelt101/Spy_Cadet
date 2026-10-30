/* Profiles, ranks, patches (achievements) and saves, adapted from Crater Crew. Everything is stored in this browser.
   ?slot=b keeps a second set of profiles, for testing two players in one browser. */
(function () {
const SC = window.SC = window.SC || {};
const SLOT = (new URLSearchParams(location.search).get('slot') || '').replace(/[^a-z0-9]/gi, '');
const KEY = 'sc1.profiles' + SLOT, SET = 'sc1.settings' + SLOT;
const load = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };

SC.COLORS = [
  {id:'navy', hex:'#5b8fd9'}, {id:'brass', hex:'#d8b24a'}, {id:'red', hex:'#e0624f'}, {id:'green', hex:'#5fbf7f'},
  {id:'teal', hex:'#4fbfb5'}, {id:'violet', hex:'#a685e0'}, {id:'orange', hex:'#ec9446'}, {id:'pink', hex:'#e47aa6'},
  {id:'sky', hex:'#6cc6e8'}, {id:'olive', hex:'#a5b04d'}, {id:'sand', hex:'#cfa877'}, {id:'silver', hex:'#b7c0ca'},
];
SC.colorHex = id => (SC.COLORS.find(c => c.id === id) || SC.COLORS[0]).hex;
SC.PICK_AVATARS = 32;

/* Ranks: XP to reach each one. Rewards never take progress away and never rank players against each other. */
SC.RANKS = [{name:'Cadet', xp:0}, {name:'Junior Codebreaker', xp:120}, {name:'Codebreaker', xp:320}, {name:'Senior Codebreaker', xp:650},
  {name:'Section Chief', xp:1100}, {name:'Station Chief', xp:1700}];
SC.rankOf = xp => { let r = 0; SC.RANKS.forEach((k, i) => { if (xp >= k.xp) r = i; }); return r; };
SC.rankInfo = p => { const r = SC.rankOf(p.xp), cur = SC.RANKS[r], next = SC.RANKS[r + 1];
  return {rank:r, name:cur.name, next:next ? next.name : null, frac:next ? (p.xp - cur.xp) / (next.xp - cur.xp) : 1}; };

const blankStats = () => ({hand:0, machine:0, wraps:0, caught:0, looked:0, recovered:0, filed:0, keys:0, filler:0, votesRight:0,
  missions:0, teamMissions:0, stars3:0, early:0, cards:0, hintsUsed:0});

/* Patches: earned once, checked after every reward. */
SC.PATCHES = [
  {id:'first', icon:'📨', name:'First message', what:'File your first decoded message.', test:s => s.filed >= 1},
  {id:'pencil', icon:'✏️', name:'Pencil and paper', what:'Strip 10 groups by hand.', test:s => s.hand >= 10},
  {id:'human', icon:'🧮', name:'Human computer', what:'Strip 100 groups by hand.', test:s => s.hand >= 100},
  {id:'noborrow', icon:'🔟', name:'No borrowing!', what:'Use the "add 10 first" trick 25 times.', test:s => s.wraps >= 25},
  {id:'div3', icon:'➗', name:'Divides by three', what:'Let the divide-by-3 check catch a slip 3 times.', test:s => s.caught >= 3},
  {id:'keeper', icon:'📖', name:'Codebook keeper', what:'Work out a word that was not in the codebook.', test:s => s.recovered >= 1},
  {id:'hunter', icon:'🔎', name:'Word hunter', what:'Work out 3 unknown words.', test:s => s.recovered >= 3},
  {id:'traffic', icon:'📻', name:'Every message counts', what:'Decode 10 everyday messages.', test:s => s.filler >= 10},
  {id:'team', icon:'🤝', name:'Teamwork', what:'Finish a mission in a team game.', test:s => s.teamMissions >= 1},
  {id:'crew', icon:'👥', name:'Station crew', what:'Finish 5 missions in team games.', test:s => s.teamMissions >= 5},
  {id:'perfect', icon:'⭐', name:'Perfect shift', what:'Get 3 stars on a mission.', test:s => s.stars3 >= 1},
  {id:'early', icon:'⏱', name:'Ahead of time', what:'Finish a timed mission with half the clock left.', test:s => s.early >= 1},
  {id:'remember', icon:'🕯', name:'Remember them', what:'Read 4 people\'s stories in the Records Room.', test:s => s.cards >= 4},
  {id:'m1', icon:'🗝', name:'The Dungeon', what:'Finish mission 1.', test:(s, p) => !!(p.missions.m1 || {}).done},
  {id:'m2', icon:'⚓', name:'Coral Sea', what:'Finish mission 2.', test:(s, p) => !!(p.missions.m2 || {}).done},
  {id:'m3', icon:'💧', name:'The water trick', what:'Finish mission 3.', test:(s, p) => !!(p.missions.m3 || {}).done},
  {id:'m4', icon:'🏅', name:'The Midway Code', what:'Finish the whole campaign.', test:(s, p) => !!(p.missions.m4 || {}).done},
];
SC.XP = {hand:3, look:1, recover:15, key:20, filler:10, vote:10, mission:60, star:15};

SC.Store = {
  db:load(KEY, {list:[], current:null}),
  settings:load(SET, {sound:true, music:true, musicVol:35, voice:true, autoVote:60}),
  save(){ save(KEY, this.db); save(SET, this.settings); },
  profiles(){ return this.db.list; },
  current(){ return this.db.list.find(p => p.id === this.db.current) || null; },
  select(id){ this.db.current = id; this.save(); },
  create({name, color, avatar, level}){
    const p = {id:'p' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name:String(name).trim().slice(0, 16) || 'Cadet',
      color, avatar, level, xp:0, stats:blankStats(), patches:{}, people:{}, read:{}, missions:{}, created:Date.now()};
    this.db.list.push(p); this.db.current = p.id; this.save(); return p;
  },
  remove(id){ this.db.list = this.db.list.filter(p => p.id !== id); if (this.db.current === id) this.db.current = null; this.save(); },
  /* Save backup as a code, like Crater Crew: works across browsers and survives cleared storage. */
  exportCode(){ return 'SC1:' + btoa(unescape(encodeURIComponent(JSON.stringify({v:1, profiles:this.db.list})))); },
  importCode(code){
    const data = JSON.parse(decodeURIComponent(escape(atob(String(code).trim().replace(/^SC1:/, '')))));
    if (!data || !Array.isArray(data.profiles)) throw new Error('bad');
    data.profiles.forEach(p => { fix(p); const i = this.db.list.findIndex(q => q.id === p.id); if (i >= 0) this.db.list[i] = p; else this.db.list.push(p); });
    this.save(); return data.profiles.length;
  },
};
const fix = p => { p.stats = {...blankStats(), ...(p.stats || {})}; p.patches = p.patches || {}; p.people = p.people || {}; p.read = p.read || {}; p.missions = p.missions || {}; };
SC.Store.db.list.forEach(fix);
SC.playerSummary = p => ({pid:p.id, name:p.name, color:p.color, avatar:p.avatar ?? null, level:p.level, rank:SC.rankOf(p.xp)});

/* Give XP and count a stat. Returns notices (new patches, a new rank) for the screen to show. */
SC.reward = (p, stat, n = 1, xp = 0) => {
  if (!p) return [];
  const r0 = SC.rankOf(p.xp);
  if (stat) p.stats[stat] = (p.stats[stat] || 0) + n;
  p.xp += xp;
  const out = [];
  SC.PATCHES.forEach(pt => { if (!p.patches[pt.id] && pt.test(p.stats, p)) { p.patches[pt.id] = Date.now(); p.xp += 25; out.push({k:'patch', id:pt.id}); } });
  const r1 = SC.rankOf(p.xp); if (r1 > r0) out.push({k:'rank', rank:r1});
  SC.Store.save();
  return out;
};
/* A finished mission: best stars are kept, and the mission's history person joins the Records Room. */
SC.finishMission = (p, mid, stars, {team, early, late}) => {
  const rec = p.missions[mid] || (p.missions[mid] = {done:false, stars:0, plays:0});
  rec.plays++; rec.done = true; rec.stars = Math.max(rec.stars, stars); rec.late = !!late && !rec.stars;
  const {m} = SC.Engine.find(mid); p.people[m.history.person] = p.people[m.history.person] || Date.now();
  p.stats.missions++; if (team) p.stats.teamMissions++; if (stars === 3) p.stats.stars3++; if (early) p.stats.early++;
  return SC.reward(p, null, 0, SC.XP.mission + SC.XP.star * stars);
};
SC.missionOpen = (p, c, i) => i === 0 || !!(p && (p.missions[c.missions[i - 1].id] || {}).done) || !!SC.Store.settings.allMissions;
})();

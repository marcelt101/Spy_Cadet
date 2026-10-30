/* The JN-25 style naval code. Every word has a 5-digit code group, and every real code group divides by 3 (the
   Japanese Navy used this as an error check, and it helped US codebreakers too). Before sending, each code group
   is hidden by adding an "additive" group from a second book, digit by digit, without carrying. The receiver
   subtracts the same additive, again digit by digit and without borrowing, and looks the code group up.
   Pure functions only, so the same file runs in the browser and in the Node tests. */
(function () {
const SC = window.SC = window.SC || {};

/* Small seeded random numbers (mulberry32), so every device builds the same messages from the same seed. */
SC.rng = seed => { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a;
  t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
SC.hashSeed = s => { let h = 2166136261; for (const c of String(s)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };
SC.pick = (r, list) => list[Math.floor(r() * list.length)];
SC.shuffle = (r, list) => { const a = list.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

const pad = g => String(g).padStart(5, '0');
const digits = g => pad(g).split('').map(Number);

SC.Code = {
  digits,
  /* Add or subtract digit by digit, with no carrying and no borrowing: 47250 + 31819 = 78069. */
  add: (a, b) => { const x = digits(a), y = digits(b); return x.map((d, i) => (d + y[i]) % 10).join(''); },
  sub: (a, b) => { const x = digits(a), y = digits(b); return x.map((d, i) => (d - y[i] + 10) % 10).join(''); },
  subDigit: (c, k) => (c - k + 10) % 10,
  digitSum: g => digits(g).reduce((s, d) => s + d, 0),
  /* A number divides by 3 exactly when the sum of its digits does, which is easy to check by hand. */
  div3: g => SC.Code.digitSum(g) % 3 === 0,

  /* One code group for every word: different groups, all dividing by 3, none starting with 0. */
  makeBook(words, seed){
    const r = SC.rng(seed), used = new Set(), book = {};
    words.forEach(w => { let g;
      do { g = String((10002 + Math.floor(r() * 29999) * 3)).slice(0, 5); } while (used.has(g) || !SC.Code.div3(g) || g[0] === '0');
      used.add(g); book[w] = g; });
    return book;
  },
  /* The additive book: a long list of random 5-digit groups. A message says where in the list it starts. */
  makeAdditives(n, seed){ const r = SC.rng(seed ^ 0x9E3779B9), out = [];
    for (let i = 0; i < n; i++) out.push(pad(Math.floor(r() * 100000))); return out; },
  encrypt(words, book, additives, start){
    return words.map((w, i) => { const code = book[w], add = additives[(start + i) % additives.length];
      if (!code) throw new Error('No code group for ' + w);
      return {word:w, code, add, cipher:SC.Code.add(code, add)}; });
  },
  decrypt(ciphers, additives, start){ return ciphers.map((c, i) => SC.Code.sub(c, additives[(start + i) % additives.length])); },
  lookup(group, book){ const w = Object.keys(book).find(k => book[k] === group); return w == null ? null : w; },

  /* What went wrong with a typed answer, for the mentor: the first digit that is off and the math for it. */
  check(cipher, add, typed){
    const want = SC.Code.sub(cipher, add), t = String(typed);
    if (t === want) return {ok:true, want};
    const i = [...want].findIndex((d, k) => t[k] !== d), c = +cipher[i], k = +add[i];
    return {ok:false, want, at:i, c, k, borrow:c < k, div3:SC.Code.div3(t)};
  },
  /* The words for one digit's sum: "8 − 3 = 5", or "2 − 7: think 12 − 7 = 5" when it would go below zero. */
  digitMath(c, k){ const d = SC.Code.subDigit(c, k); return c >= k ? `${c} − ${k} = ${d}` : `${c} − ${k}: think 1${c} − ${k} = ${d}`; },
  /* Mentor hints for one group, from gentle to the full answer. */
  hints(state){
    const {cipher, add, typed = '', tries = 0} = state, want = SC.Code.sub(cipher, add), i = Math.min(typed.length, 4);
    if (tries < 1) return 'Take each digit of the message group and subtract the digit of the additive under it.';
    if (tries < 2) return 'No carrying and no borrowing: if a digit would go below zero, add 10 first.';
    return `Digit ${i + 1}: ${SC.Code.digitMath(+cipher[i], +add[i])}. The whole group is ${want}.`;
  },
};
if (typeof module !== 'undefined') module.exports = SC;
})();

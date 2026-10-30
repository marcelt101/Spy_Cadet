/* Sound, all made live in the browser (Web Audio), so there are no sound files: typewriter keys, the teletype,
   rubber stamps, the ÷3 lamp, Morse beeps and a quiet music bed. The music engine is Crater Crew's, with darker
   1940s-radio chords and a soft clock tick when time is short. Read-aloud uses the browser's own speech voices.
   Browsers only allow sound after the first tap, so everything starts then. */
(function () {
const SC = window.SC;
const S = () => SC.Store.settings;
let ctx = null, noiseBuf = null;
const ac = () => { if (!ctx) { ctx = new (window.AudioContext || window.webkitAudioContext)();
  noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate); const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
  if (ctx.state === 'suspended') ctx.resume(); return ctx; };
function tone(f, d = .08, type = 'sine', v = .06, when = 0){
  if (!S().sound) return; try { const c = ac(), t = c.currentTime + when, o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.value = f;
    g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.0001, t + d); o.connect(g).connect(c.destination); o.start(t); o.stop(t + d + .02); } catch (e) {}
}
function noise(d = .03, freq = 3000, v = .08, when = 0, type = 'bandpass'){
  if (!S().sound) return; try { const c = ac(), t = c.currentTime + when, s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain();
    s.buffer = noiseBuf; f.type = type; f.frequency.value = freq; f.Q.value = 1.2; g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(.0001, t + d);
    s.connect(f).connect(g).connect(c.destination); s.start(t, Math.random() * .5); s.stop(t + d + .02); } catch (e) {}
}
SC.sfx = {
  click:() => tone(520, .04, 'triangle', .03),
  key:() => { noise(.025, 2400 + Math.random() * 800, .12); tone(140, .03, 'square', .02); },
  bell:() => { tone(1568, .5, 'sine', .05); tone(2350, .3, 'sine', .015); },
  teletype:(n = 6) => { for (let i = 0; i < n; i++) noise(.018, 3200, .05, i * .045); },
  stamp:() => { tone(90, .18, 'sine', .14); noise(.08, 600, .18, 0, 'lowpass'); },
  ok:() => { tone(660, .1, 'sine', .06); tone(990, .18, 'sine', .05, .08); },
  bad:() => { tone(150, .22, 'square', .035); tone(110, .25, 'square', .03, .05); },
  flip:() => { for (let i = 0; i < 4; i++) noise(.04, 1200 + i * 500, .05, i * .02, 'highpass'); },
  morse:() => { let t = 0; [1, 0, 1, 1].forEach(dah => { tone(760, dah ? .18 : .06, 'sine', .04, t); t += (dah ? .18 : .06) + .07; }); },
  win:() => [392, 523, 659, 784].forEach((f, i) => { tone(f, .3, 'sawtooth', .025, i * .13); tone(f / 2, .3, 'sine', .04, i * .13); }),
  join:() => tone(740, .12, 'sine', .05),
};

/* ---------- music ---------- */
const hz = m => 440 * Math.pow(2, (m - 69) / 12);
const CHORDS = [[45, 52, 60, 64], [41, 48, 57, 64], [43, 50, 58, 65], [40, 47, 55, 62], [38, 45, 53, 60]];
const BELLS = [69, 72, 76, 79, 81];
let mctx = null, out = null, wet = null, started = false, mode = 'calm', chord = CHORDS[0], tickTimer = null;
const vol = () => (S().music === false ? 0 : (S().musicVol ?? 35) / 100) * .5;
function init(){
  mctx = ac(); out = mctx.createGain(); out.gain.value = 0; const comp = mctx.createDynamicsCompressor(); out.connect(comp); comp.connect(mctx.destination);
  const len = mctx.sampleRate * 2.5, b = mctx.createBuffer(2, len, mctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.8); }
  const rv = mctx.createConvolver(); rv.buffer = b; wet = mctx.createGain(); wet.gain.value = .4; wet.connect(rv); rv.connect(out);
  document.addEventListener('visibilitychange', () => { if (document.hidden) mctx.suspend(); else if (vol() > 0 || S().sound) mctx.resume(); });
}
function pad(){
  chord = CHORDS[Math.floor(Math.random() * CHORDS.length)];
  const t = mctx.currentTime, len = 10, f = mctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = mode === 'tense' ? 600 : 850;
  const g = mctx.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.055, t + 3); g.gain.setValueAtTime(.055, t + len - 4); g.gain.linearRampToValueAtTime(0, t + len);
  f.connect(g); g.connect(out); g.connect(wet);
  chord.forEach(m => [-7, 7].forEach((cents, k) => { const o = mctx.createOscillator(); o.type = k ? 'triangle' : 'sine'; o.frequency.value = hz(m); o.detune.value = cents;
    const og = mctx.createGain(); og.gain.value = k ? .3 : .6; o.connect(og); og.connect(f); o.start(t); o.stop(t + len + .1); }));
  setTimeout(pad, (len - 3 + Math.random() * 2) * 1000);
}
function bell(){
  if (mode !== 'tense') { const m = BELLS[Math.floor(Math.random() * BELLS.length)], t = mctx.currentTime, o = mctx.createOscillator(), g = mctx.createGain();
    o.frequency.value = hz(m); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.025, t + .01); g.gain.exponentialRampToValueAtTime(.0001, t + 2.5);
    o.connect(g); g.connect(out); g.connect(wet); o.start(t); o.stop(t + 2.6); }
  setTimeout(bell, (6 + Math.random() * 10) * 1000);
}
/* A soft clock tick while the mission clock is nearly out. */
function tick(){ if (mode === 'tense' && vol() > 0) { const t = mctx.currentTime, s = mctx.createBufferSource(), f = mctx.createBiquadFilter(), g = mctx.createGain();
  s.buffer = noiseBuf; f.type = 'bandpass'; f.frequency.value = 4200; g.gain.setValueAtTime(vol() * .25, t); g.gain.exponentialRampToValueAtTime(.0001, t + .03);
  s.connect(f).connect(g).connect(out); s.start(t); s.stop(t + .05); } }
function apply(){ if (!mctx) return; const t = mctx.currentTime, v = vol(); out.gain.cancelScheduledValues(t); out.gain.setTargetAtTime(v, t, v > out.gain.value ? 2.5 : .4); }
SC.music = {
  start(){ if (started) return; try { init(); } catch (e) { return; } started = true; pad(); setTimeout(bell, 5000); tickTimer = setInterval(tick, 1000); apply(); },
  setMode(m){ mode = m; },
  refresh(){ apply(); },
};
const go = () => { SC.music.start(); document.removeEventListener('pointerdown', go); document.removeEventListener('keydown', go); };
document.addEventListener('pointerdown', go); document.addEventListener('keydown', go);

/* ---------- read-aloud ---------- */
let voice = null;
const pickVoice = () => { try { const vs = speechSynthesis.getVoices().filter(v => /^en/i.test(v.lang));
  voice = vs.find(v => /US/i.test(v.lang) && /male|david|guy|daniel/i.test(v.name)) || vs.find(v => /en-US/i.test(v.lang)) || vs[0] || null; } catch (e) {} };
try { pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; } catch (e) {}
SC.speech = {
  ok:() => 'speechSynthesis' in window,
  say(text, onEnd){ try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(String(text)); if (voice) u.voice = voice; u.rate = .95; u.pitch = 1;
    if (onEnd) u.onend = onEnd; speechSynthesis.speak(u); return true; } catch (e) { return false; } },
  stop(){ try { speechSynthesis.cancel(); } catch (e) {} },
};
})();

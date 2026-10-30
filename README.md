# Spy Cadet

A classroom codebreaking game set in World War II. Each student plays on their own device. Students decode real-style enemy messages, work out unknown code words together, and vote on the big decisions. The game ends in a Records Room that honors the real people who did this work.

**Campaign 1: The Midway Code** (Pacific, 1942). You join Station HYPO, the US Navy codebreaking office in a Pearl Harbor basement, and help read the Japanese Navy's JN-25 code. It has four missions:

| # | Mission | What you do |
|---|---|---|
| 1 | The Dungeon (March 1942) | Training: strip the additive, look up the code group, work out your first unknown word |
| 2 | Operation MO (April 1942) | Find where the invasion is aimed (Port Moresby) before the Battle of the Coral Sea |
| 3 | AF Is Short of Water (May 1942) | Set the famous trap that proved AF meant Midway: three team decisions, then decode the enemy's reply |
| 4 | The Battle of Midway (June 1942) | Against the clock: find the date and the direction of the attack, then place the carriers |

**Play now: https://marcelt101.github.io/Spy_Cadet/**. The root `index.html` redirects to `game/`.

To play locally, run a small web server:

```
python3 -m http.server 8000      # then open http://localhost:8000/game/
```

## How it plays

1. **Intercept.** A teletype strip of 5-digit groups arrives.
2. **Strip the additive.** For each group, subtract the additive digit by digit without borrowing (2 − 7 → 12 − 7 = 5) on a big number pad. A lamp checks the answer: every real JN-25 code group divides by 3, which the Japanese Navy really used as an error check. After a few groups by hand, the IBM strip machine can finish the message, as HYPO's punch-card machines really did.
3. **Look it up.** The codebook flips to the group and the word appears.
4. **Work out unknown words.** Some groups are not in the codebook yet. The player reads every message where the group shows up, gets a clue, and picks the meaning. A word found by one player appears in everyone's codebook.
5. **File it.** Decoded priority messages are pinned on the board.
6. **Decide.** The commander asks a question and the team votes. A wrong answer is explained and the team votes again.
7. **Outcome.** A teletype prints the result, stars stamp in, and the "What really happened" card tells the true story and adds a real person to the Records Room.

Levels (chosen on the ID badge): **Recruit** (8–10: step-by-step math, no clock), **Codebreaker** (11–13), **Cryptanalyst** (14+: every group by hand, tighter clock).

## Team games

1. The teacher taps **Host a team game**. The screen shows a room code like `SPY-K7QF` and a QR code.
2. Students make an ID badge (codenames only), tap **Join** and type the code.
3. The host picks the mission and the clock and taps **Start mission**. Everyone gets their own intercepts, and the message pool grows with the class, up to 32 players.

Networking is Crater Crew's: the host's browser is the server, and devices find each other through the free PeerJS service, then talk directly. `?net=local` uses a BroadcastChannel instead, for testing several tabs in one browser, and `?slot=b` keeps a separate set of profiles per tab.

## Code

There is no build step: plain HTML, CSS and JavaScript in `game/`.

| File | What it does |
|---|---|
| `js/codebook.js` | The JN-25 style cipher: add and subtract without carrying, the divide-by-3 check, seeded codebook and additives, hints |
| `js/content.js` | Every word the player reads: missions, messages, votes, news, history cards, people. Ready for fact-checking and translation |
| `js/engine.js` | Mission rules: builds the intercepts from a seed, hands out messages, shared word recoveries, votes, clock, stars |
| `js/game.js` | Solo, host and join; the protocol; the mission clock; rewards; the lobby |
| `js/desk.js` | The workstation |
| `js/ui.js`, `js/map.js` | Home, ID badges, settings, Records Room, teacher page, folders, the campaign map |
| `js/profile.js` | Profiles, ranks, patches and save codes (from Crater Crew) |
| `js/avatars.js` | 32 avatars plus the mentor (from Crater Crew, with 1940s hats) |
| `js/net.js` | PeerJS host and join (from Crater Crew) |
| `js/audio.js` | Sound effects, the music bed (Crater Crew's engine) and read-aloud |

Each device rebuilds the same intercepts from the mission, a seed and the player count, so only the small shared state goes over the network.

## Tests and builds

```
node tests/run-tests.js     # cipher, content checks, mission rules, robots finishing every mission with 1, 2, 7 and 32 players
python3 tools/build.py      # runs the tests, then zips game/ for itch.io into dist/
```

## Publishing

Set up like Crater Crew: there is one game, in `game/`, on the `main` branch, and GitHub Pages serves `main` straight from the repository root. The root `index.html` sends players to `game/`, and `.nojekyll` makes GitHub serve the files as they are. Pushing to `main` updates the web version.

For itch.io, run `python3 tools/build.py` and upload the zip from `dist/`.

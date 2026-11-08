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

### How devices connect

There are two ways, and the game picks one from its settings (`game/js/config.js`):

- **Classroom server (school-safe, recommended for schools).** `server/relay.js` serves the game and passes team-game messages between devices. Everything is ordinary HTTPS on port 443, from the same address as the game: **if a school's network can open the game, it can play team games.** Each device uses a WebSocket when the network allows it. If a firewall or filter breaks WebSockets, the device switches by itself to long-polling (plain web requests), which gets through strict filters and SSL-inspecting proxies. Messages are numbered and stay queued until confirmed, so a Chromebook that drops Wi-Fi for a few seconds carries on without losing anything.
- **PeerJS (Crater Crew's way).** Devices find each other through the free PeerJS service and then talk directly over WebRTC. This needs no server of your own, but school firewalls often block it: they block the PeerJS service, or the UDP traffic WebRTC needs.

The host's browser runs the game rules either way. The classroom server only passes messages along and stores nothing.

Link options for testing: `?net=local` uses a BroadcastChannel, for several tabs in one browser. `?slot=b` keeps a separate set of profiles per tab. `?relay=https://…` uses that classroom server. `?via=poll` forces the long-poll backup. `?net=peer` forces PeerJS.

### Team games at school

1. **Run the classroom server** somewhere every student device can reach. It needs Node.js 18 or later and nothing else:

   ```
   node server/relay.js            # or: docker build -t spy-cadet . && docker run -p 8080:8080 spy-cadet
   ```

   It prints its addresses. Run **one copy only**: rooms live in memory, so every device in a class must reach the same server process. If you use a cloud host that scales automatically, set it to a single instance. Put HTTPS in front of it, as most hosts do by default.
   - **A cloud host** (any service that runs a Node app or a Docker image with WebSockets) gives one address that works for every school, for example `https://spy-cadet.yourdomain.org`. Schools often block game sites (itch.io included) by category, so an address on your own domain that is not filed as "games" gets through filters best.
   - **A computer at school** (the teacher's laptop, or a small school server) also works: students open `http://<that computer's address>:8080/`. This works with no internet at all, but only if the school Wi-Fi lets devices reach each other. Many school networks block that, so try it first.
2. **Open the game from the server's address**: that copy uses the server automatically, with nothing to set. To point another copy (GitHub Pages, itch.io) at it, set `SC.RELAY_URL` in `game/js/config.js`, or build with `python3 tools/build.py --relay https://your-server`. In that case the school filter must allow both addresses.
3. **Before class**, open **For teachers → Check this network** on a student Chromebook on the school Wi-Fi. It says whether the server is reachable and whether the fast or the backup connection will be used. If it is blocked, it names the one address to ask IT to allow.

## Code

There is no build step: plain HTML, CSS and JavaScript in `game/`, plus the optional classroom server in `server/`.

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
| `js/net.js` | Host and join: the school-safe relay client (WebSocket, falling back to long-poll), PeerJS (from Crater Crew), the network check |
| `js/config.js` | Where the classroom server is. Empty means PeerJS |
| `../server/relay.js` | The classroom server: serves `game/` and relays messages. Plain Node.js, no dependencies |
| `js/audio.js` | Sound effects, the music bed (Crater Crew's engine) and read-aloud |

Each device rebuilds the same intercepts from the mission, a seed and the player count, so only the small shared state goes over the network.

## Tests and builds

```
node tests/run-tests.js     # cipher, content checks, mission rules, robots finishing every mission with 1, 2, 7 and 32 players
node tests/relay-test.js    # classroom server and the game's relay client: WebSocket, long-poll, dropped lines, kicks, leaving
python3 tools/build.py      # runs both, then zips game/ for itch.io into dist/ (add --relay URL to use a classroom server)
```

## Publishing

Set up like Crater Crew: there is one game, in `game/`, on the `main` branch, and GitHub Pages serves `main` straight from the repository root. The root `index.html` sends players to `game/`, and `.nojekyll` makes GitHub serve the files as they are. Pushing to `main` updates the web version.

For itch.io, run `python3 tools/build.py` and upload the zip from `dist/`.

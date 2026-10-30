# Spy Cadet: design plan

This plan is the trimmed version of the original *Code War* white paper. It aims at classrooms first: a teacher hosts and every student plays on their own Chromebook.

## Scope

- **Five campaigns**, each a short series of missions that fits one or two class periods, and each built around one code system:

| # | Campaign | Code system | Big idea |
|---|---|---|---|
| 1 | **The Midway Code**, Pacific 1942 (built) | JN-25 codebook with additives | Traps and teamwork reveal what a code means |
| 2 | Battle of the Atlantic, 1941–43 | Enigma | A strong machine fails through predictable habits |
| 3 | North Africa, 1941–42 | The stolen Black Code | A stolen codebook beats any cipher |
| 4 | Europe 1944: D-Day to the Bulge | Code Talkers and radio silence | A language, or silence, can be the best code |
| 5 | Eastern Front 1943: Kursk | One-time pad | Perfect systems fail when people cut corners |

- **Cut from the white paper:** two-player message codes, Purple, Lorenz, SIGSALY and the 45-mission list.

## Principles (unchanged)

1. Honor the people: real people appear only on history cards and in the Records Room, with short, accurate stories.
2. Get the history right, and say plainly what the game simplified.
3. No graphic violence and no casualty counts as scores. Losses are mentioned honestly.
4. Learn by doing: every mistake gets an explanation, never just "Wrong".
5. Kid friendly: big buttons, short sentences, read-aloud, hints, no fast typing.

## The mission loop

A mission is a list of phases in `content.js`:

- `decode`: the priority messages that must be read, plus everyday "filler" traffic. The filler pool grows with the class, so all 32 players have something to do.
- `vote`: a question with one right answer and an explanation for every answer.

The engine (`engine.js`) is the same for every mission, so a new mission is content, not code. A new campaign needs one new cipher module with the same shape as `codebook.js`.

## Team play

- The host's browser runs the rules and sends the shared state. Each device rebuilds the intercepts from a seed.
- **Shared codebook:** an unknown word worked out by one student appears for everyone, credited to them. This is the main way students cooperate.
- **Votes:** the team goes with the most popular answer. A tie goes to the answer that got its first vote earliest. A wrong answer is explained and the team votes again, which is a natural moment for discussion.
- **Nobody waits forever:** if someone drops out, their message goes back in the pool, and the host can close a vote with **Decide now**.
- **Next step for teams:** roles (codebreakers, signals operators, commanders) and an opposing Japanese team are planned once the solo and co-op feel is right.

## Rewards (from Crater Crew)

XP, six ranks (Cadet to Station Chief), 17 patches, best stars per mission, and real people's stories in the Records Room. Rewards never take progress away and never rank children against each other.

## Open questions

- Who fact-checks the history cards and the people list before release?
- Which photos to use (see `ASSETS.md`)?
- Recorded voices instead of the browser's speech voice?
- Japanese-side missions for campaign 1, or move on to campaign 2 first?

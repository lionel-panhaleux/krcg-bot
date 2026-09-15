# Dogmas

Paradigms chosen by the human. Ingress challenges an incoming ask against this page; egress checks
the landed change against it. Overturning one is valid work; violating one silently is not.
Observed in the code; a dated line is a decision Lionel took, on that date.

## Code

**Tight, local, KISS.** No patterns, abstractions or indirection for elegance's sake — they must earn
their keep. Don't write for a human reader's comfort; keep it terse for agentic workers.

**One module.** The whole bot is `src/krcg_bot/__init__.py`, plus a three-line `__main__.py`. Extract
a module only behind an interface much narrower than what it hides. Layering ceremony — clean-arch,
hexagonal — is an anti-pattern here: it mass-produces shallow modules, which are pure token cost and
misuse surface.

**KISS means hazard-avoidance, not small diffs.** Big rewrites are cheap; the coding loop is agentic
and rewrites fast. What is expensive is *hazard* — non-local interdependency, behaviour not evident
where it lives, traps for a future agent without today's context. Prefer the design a fresh agent
can understand from the files in front of it. The amount of code needing a rewrite is never a reason
to defer.

**Repetition over false abstraction.** Similar-looking but causally unrelated code stays repeated.
Never factor on resemblance.

**Comments are for traps only.** The wiki holds the why, the code shows the how. A comment is
justified only by a subtle non-local constraint invisible at the point of reading. No narration, no
changelogs, **no TODOs** — discovered work goes through ingress or gets done now.

**Raw hikari, no command framework.** A `hikari.GatewayBot` with `bot.listen()` listeners. Dispatch
is two tables: `COMMANDS_TO_REGISTER` by command name, `COMPONENTS` by the first 6 characters of
`custom_id` — a new command or button is an entry there. `os.getenv` at point of use, no settings
object. `__debug__` sets the log level, nothing else. **Card facts come from `krcg`**, never
hardcoded.

## Errors

**A refusal the reader can act on is a `CommandFailed(msg)`**, answered ephemerally with `msg`.
Anything else is logged with its traceback and answered "Command error". Handlers look cards up
through `_card()` and parse trails through `_parse_stack()`, which raise `CommandFailed`: a bare
`CARDS[id]` or `int()` shows "Command error" on exactly the old buttons a release leaves live
([buttons.md](buttons.md#old-buttons-after-a-deploy-2026-07-29)). **Autocomplete never raises** —
nothing can answer it ([discord.md](discord.md#interactions)).

## State

**No database, and no state a restart cannot rebuild** (2026-07-27). The corpus reloads on start; a
button carries its own trail. What lives in memory is only what a restart may lose: guild emojis,
fetched again as guilds become available; the expiry watchers, which heal themselves; the
autocomplete cache.

## Testing

**Few tests, high coverage of behaviour.** Test what the product does at its boundary — the answer
`/card` draws, its buttons, autocomplete, Discord's limits, the failure modes that matter — never how
it does it. Agents don't make local mistakes, they make non-local ones: unit tests of internals
calcify implementation and tax every change, while integration and non-regression tests survive
refactors.

- A test is the executable slice of this wiki: each traces to a claim in [product.md](product.md) or
  [buttons.md](buttons.md), or a limit in [discord.md](discord.md). One that maps to no claim is
  evicted.
- **Tests run against the live corpus, always** (2026-07-26): no committed card fixture, and no
  synthetic card built to reach a branch the corpus cannot produce. Accepted, not a gap to close: the
  suite needs the network, a KRCG static-server outage reds unrelated changes, and the component caps
  ship with no test that fills them. Cards are picked by shape (`find()`), never by name; assertions
  are on shape and limits, never card text — upstream renames cards more often than it changes what
  a card is.
- **Mocks of our own code are banned.** Two stand-ins exist, each for a third party: the conftest
  makes krcg's local loaders raise, so `load_online`'s silent fallback is loud rather than a green
  suite on packaged data ([corpus.md](corpus.md#loading)); and `FakeInteraction` stands in for
  hikari's `AutocompleteInteraction`, its signature pinned by a test. The suite never reaches
  Discord.
- **What the suite does not cover** is verified another way, or said to be unverified: the expiry
  watcher needs a 14.5-minute wait and a race to reach its branches — a change there is driven under a
  virtual clock outside the suite, never argued; the `card`, `switch_card` and `make_public` handlers
  are verified by running the bot, `just serve` with the dev token against a test guild.
- **Weakening or deleting a test is an egress rejection** unless the wiki-declared behaviour changed.

`just lint`, `just typecheck` and `just test` pass on every landing.

## Dependencies

Prefer what is already here, then a few lines, then a dependency. `uv.lock` is the pin; only
`just update` moves it. The `hikari <3` and `krcg <6` ceilings are deliberate: bumping either past a
minor is a code change ([discord.md](discord.md#hikari-traps), [corpus.md](corpus.md)).

## Records

**No changelog.** Git history and the release notes GitHub generates are the record. *(2026-09-15:
`CHANGELOG.md` had stopped at 4.4 while 4.10 shipped.)*

**The README is for humans**, and outside wiki lint. It carries no badge restating a
`pyproject.toml` fact — those drift with nothing to catch them — except the Python floor, which a
contributor needs; the Test badge reads from Actions (2026-07-26). The Dark Pack attribution in the
README and on every card answer is not optional.

## Claims

**Tech claims: current docs first** (context7, the raw source), never recall. A failed fetch is not
an absence — record "unverified", never "undocumented" (2026-07-29). **Game-domain claims: the `vtes`
skill**, never recall.

## Commits

**Trunk-based**: commit straight to `main`, no feature branches. Two or three agents may work
parallel board lines on `main` — each claims its line, stays aware of siblings, keeps to its own
commits; imperfect commit isolation is acceptable when files overlap.

Describe the change itself in the message. When a commit fixes a GitHub issue, close it with a
`Fixes #N` line just above the trailers.

## Releases and deploys

**`just release` is the only way a version moves** (`major.minor`, default minor bump). Pushing,
releasing and deploying restart or reach the public bot: all three are the human's call.

**No release until CI is green on the remote** (2026-07-26). A gate, not a preference.

**One artifact per release, and nothing else is deployable** (2026-07-26). The GitHub release carries
the wheel, and both CI and `just deploy` converge *that file*: what runs always answers to a tag, and
rollback is redeploying an older one. Rebuilding at deploy would be correct — builds are
byte-reproducible — and was rejected anyway: two artifacts claiming to be one release. Accepted:
trying a change on the host means cutting a release.

**Deploys live in this repo**, `ansible/`, never in a shared deploy repo (2026-07-26): the bot has no
listener and no database, and `server-setup` ships only the host foundation and the `nginx_site` and
`postgres_db` roles. A published release deploys from CI; the laptop can converge the same wheel.

**No PyPI, no self-hosting** (2026-07-26): one hosted instance. The `krcg-bot` PyPI project is
archived — **never yank or delete it**. A freed name is a credential-harvest squat: the package takes
a `DISCORD_TOKEN`, and whoever installs a squatted `krcg-bot` is exactly the self-hoster this project
stopped serving.

## Human inflexion points

Interrupt the human only for: a dogma or paradigm choice (short option set plus a recommendation), an
irreversible or outward-facing action (push, release, deploy, answering an issue), a genuine change to
product scope, or an egress deadlock after two rounds. Everything else proceeds. HitL effort goes
into the harness, not the code — the ratchet turns a correction into a standing rule.

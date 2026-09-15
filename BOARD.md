# Board

What must change. The goal is zero. **Completion is deletion** — no closed state, no archive; git
history is the record. Context lives in [`wiki/`](wiki/index.md), never here: a line that cannot be
completed is documentation, and belongs on a wiki page instead.

**Order is priority**, and priority is decided by these rules, top down:

1. **Blocks someone else** — another person, another repo, another line.
2. **User-visible breakage.**
3. **User-visible feature.**
4. **Internal cleanup.**

Ties break to the smaller line. An item waiting on someone is not a state: it is a dated
follow-up ("chase @someone, 12 Oct"), owned by whoever wrote it.

---

- Settle gateway vs HTTP interactions endpoint. Lionel: "there are good tunneling solutions I think discord itself documents to achieve this". Read Discord's current docs whole (the raw `.mdx`) on running an interactions endpoint during development; done when `wiki/discord.md` §Interactions states the dated, sourced answer in place of "unverified", and — if it removes the testability objection — the switch is put to Lionel as a dogma change (it reshapes the runtime, hosting and `ansible/`). Doc-impact: `discord.md`; `dogmas.md` only if Lionel switches.

<!-- cycles-since-upkeep: 0 -->

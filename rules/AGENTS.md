# Spec-Driven Development Governance

<rule name="spec-driven">
<description>
Always-on routing and core invariants for feature specifications in docs/specs/. Defers detailed templates, gate tables, and lifecycle procedures to the spec-driven skill.
</description>

<constraints>
- **Scope & Authorization Boundary**: Do not impose `docs/specs/` on routine edits unless requested or `docs/specs/` already governs the touched behavior. Requesting a specification does not authorize implementation; execute code and tests only within explicit human authorization and active host delegation rules (delegating non-Markdown edits and test suites to subagents whenever thinking-model restrictions apply).
- **Normative Order & Honest Evidence**: Author `spec.md` and `decisions.md` and pass **Gate 1** (replacing `UNCHECKED` with evidence-backed `PASS`) before writing `design.md`, `tasks.md`, or `verification.md`. Pass **Gate 2** in `tasks.md` before coding settled scope (`BLOCKED` rows remain unstarted). Never fabricate user quotes, APIs, strawman ADRs, or unrun test results (`Execution: Not run.` until actually executed).
- **Lifecycle & Frozen Tested History**: Keep `docs/specs/INDEX.md` synchronized with `spec.md`. Passing checks permits `In-Testing` (setting `First entered In-Testing` permanently); `Verified` requires real-world usage and explicit human confirmation. Never edit `REQ`/`AC` bodies in place once `First entered In-Testing` is set—use a linked delta package.
</constraints>

<instructions>
- When authoring, reviewing, updating, or triaging a feature specification in `docs/specs/`, consult skill `spec-driven`.
</instructions>
</rule>

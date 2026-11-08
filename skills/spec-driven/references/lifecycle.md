# Lifecycle and revision guidance

Read this before changing an existing specification, triaging a defect, or updating status. The specification's status and the index must agree. The specification's lifecycle history records why they changed; verification contains the supporting observations.

## States and evidence

| State | Entry condition |
| --- | --- |
| Planning | Authoring or revising the governing requirements/design; required decisions or validation are incomplete. |
| In-Progress | Gates are complete for the authorized scope and explicit implementation authorization is recorded; or an authorized Case 1 fix has reopened the package. Owner-deferred tasks remain blocked. |
| In-Testing | All tasks are complete, no blocked criteria remain, and applicable checks have passed with actual evidence. Real-world evaluation is pending or underway. |
| Verified | Real usage evidence exists and the human explicitly confirms the feature works for the intended scope. Tests alone are insufficient. |
| Superseded | An implemented replacement specification explicitly replaces this entire package. A proposed replacement alone is insufficient. |
| Abandoned | The human explicitly cancels the work. Preserve its history and any actual implementation evidence. |

On every transition, update `spec.md` and `INDEX.md` together and append a dated reason/evidence record. Set `First entered In-Testing` on first entry and retain it forever. Preserve all previous approvals and test runs; a past approval of correctness does not verify a new fix. Record what approval covers instead of copying a stale approval onto new scope.

An explicit instruction to implement an agreed package is authorization; do not demand a specific word or ask again for the same scope. Approval of a plan is not proof that checks ran. Do not execute unapproved material changes or unresolved product decisions. A failed check prevents promotion; report environmental blockers honestly instead of inventing a passing result.

## Select the revision route before changing status

Inspect `First entered In-Testing`, the lifecycle history, and actual verification records. A reopened `In-Progress` package may already have reached testing. For older packages without the field, infer from recorded history and populate it; if evidence is inconclusive, clarify before altering normative bodies or use a linked delta to preserve them.

- **Never reached testing:** Amend requirements in place when intent changes. Preserve existing IDs for the same requirement; allocate new IDs for distinct requirements/criteria and never repurpose existing ones. Record the reason, invalidate affected gate results, and return the package to `Planning` before revising dependent work.
- **Reached testing at least once:** Keep existing requirement and acceptance-criterion bodies unchanged. Create a linked delta package for changed behavior, assigning new requirement IDs and recording previous contracts. The delta starts in `Planning`; it does not reset the parent's testing history or automatically change the parent's status. Add lifecycle/reference annotations outside the frozen bodies.
- **Whole-package replacement:** Explicitly state which package is replaced and cover its retained behavior as well as deliberate removals. Do not mix whole replacement and partial-change claims for the same target.

Changing metadata, appending approval/history entries, and adding relationship annotations does not change a requirement's body. Accepted ADR bodies remain historical: append a new decision when the approach changes and link the old entry to it. Proposed decisions may be refined before acceptance.

## Related specifications and activation

Use links labelled `Changes`, `Retires`, or `Replaces` with explicit feature/requirement IDs. Distinguish planned relationships from implemented ones. A parent may list a proposed delta under related specifications without presenting it as the current contract.

When a delta reaches `In-Testing`, record that its changes are implemented, link both packages, and identify the current requirement for each changed behavior by adding a 1-hop Current contract annotation outside the parent requirement's frozen body (pointing directly to the latest implemented requirement). Keep earlier relationship history; when several deltas affect the same requirement, update current-requirement annotations to link directly to the latest implemented requirement. A partially modified parent remains active for unaffected requirements. A whole replacement reaching `In-Testing` moves its parent to `Superseded`.

If a delta is abandoned before implementation, mark its proposed relationship abandoned; it never becomes the current contract. If an implemented delta is later cancelled, cancellation does not undo code: record the actual remaining behavior and plan any rollback as separate authorized work. Do not silently repoint references to an unverified assumption about rollback.

Retiring behavior requires a new, attributable requirement describing the observable outcome and migration, with success and relevant boundary criteria. Use the retirement pattern in [templates.md](templates.md); map it through design, tasks, and verification like any other requirement.

## Three defect cases

Classify the observed cause, not just where the failure surfaced. If the cause is uncertain, investigate and record the uncertainty before choosing a route. A compound defect can be split into separately classified changes.

### Case 1: implementation defect

The requirements and design remain correct; code, tests, or delivered artifacts do not satisfy them.

1. Preserve normative requirement/AC bodies, accepted ADR bodies, and the valid design. Mint no requirement IDs.
2. Within authorization to fix the defect, reopen the affected package as `In-Progress`; update its header, catalog, and lifecycle history. Add an unchecked reproducer/fix task citing existing criteria and update Gate 2 mappings to include it. Existing valid Gate 1 evidence remains applicable.
3. Reproduce the failure when feasible, make the fix, and run the relevant checks. Append genuine failure/success evidence; never erase the earlier run.
4. Once all work and checks pass, return to `In-Testing`. Preserve the original first-testing date. Obtain new real-world confirmation before returning to `Verified`.

### Case 2: design or architecture defect

The observable requirement is still right, but its proposed approach fails in practice.

1. Preserve requirement/AC bodies and IDs. Set the affected package to `Planning`, retaining its testing history.
2. Append a replacement ADR for an accepted choice, or refine a still-proposed choice; record the observed constraint and viable approach. Invalidate affected gate results.
3. Revalidate normative rationale in Gate 1 before updating dependent design/tasks/verification plans; then rerun Gate 2. Preserve past execution evidence.
4. Present changed tradeoffs and obtain authorization if existing approval does not cover them. Resume authorized work, then pass through `In-Testing` again.

### Case 3: missing or incorrect requirement

The desired observable behavior itself must change.

1. Pause affected implementation and determine whether the package has ever reached testing **before** modifying its status or content.
2. Amend a never-tested package in place (preserving IDs for updated requirements and minting new REQ-NNN IDs for distinct added requirements), or create a linked delta for a previously tested one (minting new REQ-NNN IDs for every changed, added, or retired requirement — unlike Case 1 and Case 2, which mint zero new requirement IDs). Record honest intent and changed/added/retired behavior using the patterns in the templates.
3. Resolve material product questions with the owner. Re-run Gate 1, derive the changed design/tasks/verification plans, and re-run Gate 2. Leave unaffected history intact.
4. Resume only within explicit authorization for the revised scope. Apply relationship/status updates when implementation evidence warrants them; do not mark a proposed delta or its parent verified.

## Owner-deferred decisions

An explicit owner deferral can permit design exploration. It cannot justify invented behavior or execution of dependent tasks. Record the affected criteria and transitive task dependencies as `BLOCKED` in Gate 2. Other independent work can proceed only when its requirements are settled, the remaining checks pass, and its scope is authorized.

After the owner answers, append the resolution, finalize the requirement and dependent plan, and rerun affected gates. If the package has already reached testing, resolve changed normative behavior through a delta. No package with unresolved criteria or unfinished tasks may enter `In-Testing` or `Verified`.

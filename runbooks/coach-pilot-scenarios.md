# Coach pilot rehearsal scenarios

Status: synthetic rehearsal ready; moderated real-coach evidence pending.

This runbook exercises one canonical play from design through outcome. It uses
the local synthetic organization only and does not approve production, activate
providers, or represent real players or opponents.

## Scenario: Dagger from decision to outcome

1. Head coach opens `/app/playbook`, selects `PD-DEMO-OFF-DAGGER`, and confirms
   the program lens is **Head coach**.
2. Head coach opens the Play Designer tutorial, reviews the call purpose, and
   confirms the design is a draftable structured play rather than an image.
3. Offensive coordinator changes the Dagger read or protection and records a
   review comment. Confirm the version/review state changes visibly.
4. Defensive coordinator opens `PD-DEMO-DEF-COVER3`, authors or reviews the
   opposing Cover 3 buzz/TEX look, and checks the legality findings.
5. Position coach opens the teaching view, filters to QB or WR, and verifies
   that unrelated assignments are dimmed while the selected role remains
   readable.
6. Player opens `/app/player`, reviews the Dagger lesson, steps through the
   read reveal, and completes the synthetic quiz.
7. Practice staff opens `/app/practice`, links Dagger to the 7-on-7 period,
   reviews reps and attendance, and records the practice outcome.
8. Staff opens `/app/film`, selects the synthetic third-down clip, and confirms
   the observation links back to the play and the defensive rotation.
9. Game-plan owner opens `/app/game-plan`, reviews the evidence-linked thread,
   and confirms the release remains human-gated.
10. Coach opens `/app/delivery`, selects the call-sheet delivery task, and
    runs export preflight before requesting a packet.
11. Player reopens the approved teaching view and verifies that the player
    artifact is filtered to the approved role and does not expose staff-only
    notes.
12. Analyst opens `/app/analytics`, records or inspects the synthetic outcome,
    and confirms the outcome references the play, practice/film evidence, and
    its uncertainty.

## Evidence to capture

- Screenshot or recording for each workspace transition.
- Play design ID and revision at every state change.
- Role/lens used for each task.
- Validation findings and any explicit coach override.
- Tutorial completion state and restart behavior.
- Export preflight result and source manifest hash.
- Player-visible versus staff-visible content.
- Outcome record and linked evidence references.

## Pass criteria

- No user needs to guess which workspace owns the next action.
- Every state-changing action shows its owner, scope, and current status.
- Synthetic values are visibly identified as synthetic.
- A player cannot see staff-only notes through the player view.
- No approval, publishing, export, or production action is silently implied.
- The complete chain can be followed from play design to outcome without
  copying IDs into a separate system.

## Human pilot boundary

Moderated coach, coordinator, position-coach, and player sessions remain
required before production claims. The moderator must use approved real-team
data or a clearly labeled pilot dataset, record usability metrics, and preserve
the owner’s decision about whether any finding becomes an implementation change.

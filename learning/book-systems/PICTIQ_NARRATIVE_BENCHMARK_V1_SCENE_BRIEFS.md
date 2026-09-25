# Pictiq Narrative Benchmark V1 — Scene Briefs

Status: design-only benchmark package. No images or Pictiq/book changes are made here.

## Scope and rules

Each brief tests semantic scene reading. Conventional drawing carries characters, objects, setting, and action; the Pictiq layer carries semantic relations where the current vocabulary can carry them. No written dialogue, captions, legend, invented glyphs, or grammar extensions are allowed. Bare adjacency remains contextual association, and panel order does not assert causality.

## Jekyll & Hyde

### Candidate scenes

1. **J-1 — Utterson and the will.** Utterson reads Jekyll's will, notices Hyde, and approaches a locked door. Tests document, secrecy, and knowledge; transformation is weak.
2. **J-2 — Lanyon witnesses the draught.** Lanyon sees Jekyll drink and become Hyde, then seals a written account. Strongest identity, knowledge, transformation, and same/different test. **Selected.**
3. **J-3 — Poole at the cabinet.** Poole hears a changed voice and sees a threshold figure but refuses to identify it. Tests uncertainty and secrecy; identity is indirect.

Placement restriction: **POST-REVEAL ONLY**. The selected scene reveals the transformation.

### Selected scene: J-2 (five panels)

| Panel | Narrative meaning | Drawn scene | Pictiq layer and placement | Density / status |
|---|---|---|---|---|
| 1 | Lanyon observes Jekyll in the laboratory. | Lanyon, Jekyll, glass, cabinet and door. | person_generic near each human; eye_look from Lanyon toward Jekyll; rel_here at the laboratory focal point. | Medium; canonical, identity contextual. |
| 2 | Jekyll initiates the change while Lanyon watches. | Jekyll raises the draught; Lanyon watches. | eye_look, action_change, person_generic, time beside the action beat. | Medium; canonical. |
| 3 | The same body changes into Hyde; the witness recoils. | Matched pose before/after, visible body continuity, Lanyon recoiling. | action_change between two person_generic figures; punct_question by Lanyon. | High; canonical operators, same-person relation is drawing/composition only. |
| 4 | Hyde is present; Lanyon is looking back and cannot safely name what he saw. | Hyde at the cabinet, Lanyon at the threshold. | eye_look, person_generic, optional punct_question. | Low; identity and uncertainty are approximate. |
| 5 | Lanyon writes and seals a private account rather than speaking. | Desk, page, pen, sealed envelope. | action_write, media_text, rel_here; logic_no and comm_speak may mark not-spoken only as an approximate composition. | Medium; document is canonical, withheld knowledge is approximate. |

Semantic target: witness knowledge, transformation, identity continuity, and withheld written testimony.

Current limitations: no canonical universal same-person, identity-continuity, uncertainty, secrecy, or causality glyph. action_change expresses change but not who remains the same. logic_no is negation, not uncertainty. The panel sequence suggests order only.

Change candidates: J-1 same entity across transformation; J-2 witness knows but does not disclose. Both require proposal and human review before any vocabulary change.

Image brief: five-panel, high-contrast Victorian gothic laboratory; recurring Lanyon and Jekyll/Hyde; clear matched pose in panel 3; desk and sealed account in panel 5; no text, dialogue, captions, or glyphs in generated art; leave clean overlay positions.

Canonical overlay assets: person_generic.svg, eye_look.svg, action_change.svg, media_text.svg, action_write.svg, punct_question.svg, logic_no.svg, rel_here.svg, time.svg. Do not invent Jekyll, Hyde, Lanyon, or same-person assets.

## No Further Claims / Bracken Ford

### Candidate scenes

1. **B-1 — The regulator morning.** An ostrich escapes, a dog pursues it, the damaged gas regulator creates a partial witness scene, and later rumor becomes an official report. **Selected.**
2. **B-2 — The missing contractor bag.** A safety incident is reconstructed from objects and testimony; uncertainty is strong but rumor is weaker.
3. **B-3 — The mutated receipt/report.** A small record changes as it passes between people; strongest record test, weakest physical chain.

### Selected scene: B-1 (five panels)

| Panel | Narrative meaning | Drawn scene | Pictiq layer and placement | Density / status |
|---|---|---|---|---|
| 1 | Physical event at dawn: bird, dog, regulator, and Eli's fallen bike share one site. | Damaged gas regulator, bird/dog aftermath, Eli and bike. | nature_animal at the animal; place_gas at regulator; person_generic by bike; eye_look for the visible site. | Medium; canonical except species/identity carried by drawing. |
| 2 | Mrs Bell sees only a subset and infers danger. | Mrs Bell at a distance; Eli hidden; gas site and dog/bird remains. | eye_look toward place_gas; place_gas; punct_question; comm_speak for her call. | Medium; direct observation vs inference is approximate. |
| 3 | The shop crowd converts partial facts into a confident rescue/eagle story. | Counter, several tellers, receipt under the till. | comm_speak among person_generic; nature_animal; punct_question; media_text near receipt. | High; rumor/social transmission is not canonical. |
| 4 | Police and utility staff establish a narrower account. | Officer, utility worker, recovered Eli, report on patrol car. | safety_police, place_gas, media_text, action_write, optional punct_question. | Medium; report is canonical as an object, authority status is drawn. |
| 5 | Official record and public story coexist with unresolved gaps. | Foreground narrow report; background oversized winged public version. | media_text, rel_here, tentative logic_no, state_dead only if the drawn remains warrant it. | High; correction, evidential status, and causality remain approximate. |

Semantic target: observation → inference → rumor → official record, while preserving deliberate ambiguity.

Current limitations: no canonical rumor, official-record, evidential-status, uncertainty, or causality glyph. A sequence does not prove that one event caused another. Do not use logic_no as a generic “not sure” mark.

Change candidates: B-1 evidential uncertainty/not observed; B-2 rumor/social transmission; B-3 official record/correction; B-4 causality. These are candidates only, not vocabulary additions.

Image brief: five-panel black-and-white contemporary small-town civic documentary; recurring bird, dog, regulator fence, Mrs Bell, Eli, and officer; no text or fake glyphs; maintain the distinction between what is seen, repeated, and recorded; leave canonical overlay positions.

Canonical overlay assets: nature_animal.svg, place_gas.svg, person_generic.svg, eye_look.svg, punct_question.svg, comm_speak.svg, media_text.svg, safety_police.svg, action_write.svg, state_dead.svg, rel_here.svg, optional time.svg.

## Evaluation protocol

Generate the scene art first without symbols. Composite only verified canonical SVG assets in a separate overlay pass. Evaluate blind before showing the guide-informed layer.

Blind questions: what happened first; what is directly observed; what changed; who is watching; which details are repeated; what does the final record establish; what remains unknown. Guide-informed questions add whether same identity, withheld knowledge, rumor, and record correction are recovered.

Success requires the minimum event chain plus the intended relation. Failure is a generic scary-person, bird/dog, police, or laboratory image without the tested semantic relation. Record panel-level loss, ambiguity, false inference, and any proposed vocabulary pressure.

Potential placement: Jekyll as a post-reveal interstitial; Bracken Ford as an opening-anchor interstitial after the first incident or as a later record divider.

## Hard stop

This file defines briefs and evaluation only. It does not generate art, alter the Pictiq vocabulary, modify either manuscript, create comics, or publish anything.

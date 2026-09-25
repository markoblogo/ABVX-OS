# Pictiq Narrative Benchmark V1 Proposal

## Purpose

Test whether a small black-and-white Pictiq comic can convey narrative relations without relying on decorative appeal, undisclosed text, or uncontrolled vocabulary growth. This is a proposal only; it changes no Pictiq artifact.

## Stress-test domains

| Book context | Relations to test |
| --- | --- |
| Jekyll & Hyde — Toki Pona Edition | identity, same/different person, transformation, secrecy, chronology, knowledge |
| No Further Claims | observation, inference, rumor, uncertainty, official record, contradiction, causality |

## Comic-insert hypothesis

An approved book may receive 3–5 inserts only if each earns its page cost. Candidate placements: a frontispiece, part transition, structural turn, pre-climax, and closing image. Default panel count is 4–5, not a requirement.

## Evaluation dimensions

1. Blind interpretation.
2. Task/narrative comprehension.
3. Exact semantic recovery.
4. Learned performance after a short guide.
5. Ambiguity rate.
6. Text dependence.
7. New-vocabulary pressure.
8. Whether the insert changes reading/comprehension enough to justify production cost.

## Vocabulary-growth control

Use only current canonical Pictiq vocabulary and operators. If a scene cannot be rendered, log a PICTIQ_CHANGE_CANDIDATE containing the missing relation, attempted composition, ambiguity, and evidence. It is reviewed separately from the book and does not alter Pictiq automatically.

## Evidence capture

For each candidate record: book, source scene, narrative function, Pictiq vocabulary, composition rules, panel count, author intent, blind interpretation, comprehension result, ambiguity, text required, what was lost, reusable grammar lesson, and any change candidate.

## Proposed first two samples

1. **Jekyll:** four panels testing identity/transformation and who knows the secret. Compare blind interpretation with guide-informed interpretation.
2. **Bracken Ford:** four panels testing witness observation → rumor → official record, with one deliberate ambiguity tracked rather than silently repaired.

Success requires comprehension of the intended relation by a defined review group without new vocabulary. Attractive artwork alone is not success.

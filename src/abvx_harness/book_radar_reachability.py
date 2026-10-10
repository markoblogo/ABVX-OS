"""Read-only calibration projections; never a production or collection authority.

Witness annotations require retained references. This module checks provenance,
not the truth of human semantic annotations, and does not infer sales from ranks.
"""
from datetime import date
from hashlib import sha256
from pathlib import Path

from .harness import ValidationError
from .schema_validation import load_draft_2020_12_validator

SCHEMA = Path(__file__).resolve().parents[2] / 'schemas/BOOK_RADAR_REACHABILITY_CALIBRATION_SCHEMA_V1.json'


def validate(case, root=None):
    errors = list(load_draft_2020_12_validator(SCHEMA).iter_errors(case))
    if errors:
        raise ValidationError('Reachability calibration: ' + errors[0].message)
    refs = {r['id']: r for r in case['evidence']}
    if len(refs) != len(case['evidence']):
        raise ValidationError('Duplicate evidence id')
    date.fromisoformat(case['as_of'])
    if case['cutoff'] is not None and date.fromisoformat(case['cutoff']) > date.fromisoformat(case['as_of']):
        raise ValidationError('Cutoff after assessment')
    for w in case['witnesses']:
        if not w['evidence_ids'] or not set(w['evidence_ids']) <= refs.keys():
            raise ValidationError('Witness requires resolved evidence')
        if w['publication_date'] is not None:
            date.fromisoformat(w['publication_date'])
        if w['knowledge_date'] is not None:
            date.fromisoformat(w['knowledge_date'])
    if case['own_validation_date'] is not None:
        date.fromisoformat(case['own_validation_date'])
    if root is not None:
        root = Path(root).resolve()
        for ref in refs.values():
            path = (root / ref['path']).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != ref['sha256']:
                raise ValidationError('Evidence missing, changed or outside root')
    return case


def assess(case, root=None):
    validate(case, root)
    eligible = []
    for w in case['witnesses']:
        if w['knowledge_date'] is not None and w['knowledge_date'] > case['as_of']:
            continue
        if case['cutoff'] is not None and (w['knowledge_date'] is None or w['knowledge_date'] > case['cutoff']):
            continue
        age = None if w['publication_date'] is None else (date.fromisoformat(case['as_of']) - date.fromisoformat(w['publication_date'])).days
        if all(w[k] == 'SUPPORTED' for k in ('identity', 'relevance', 'organic', 'context')) and age is not None and 0 <= age < 180:
            eligible.append(w)
    nonincumbents = [w for w in eligible if w['creator'] == 'NEW_OR_WEAK' and w['release'] == 'NEW_WORK']
    activity = [w for w in eligible if w['activity'] in ('BOOKS_BSR', 'KINDLE_BSR', 'VERIFIED_PAID')]
    repeated = [w for w in eligible if w['repeat'] == 'SUPPORTED']
    research_witnesses = [w for w in eligible if w['creator'] != 'DOMINANT' and w['release'] not in ('NEW_EDITION', 'NEW_FORMAT')]
    own_available = case['own_validation_date'] is not None and case['own_validation_date'] <= (case['cutoff'] or case['as_of'])
    ladder = {'R0': 'UNKNOWN' if not eligible else 'OBSERVATION_AVAILABLE',
              'R1': 'SUPPORTED' if eligible else 'UNKNOWN',
              'R2': 'SUPPORTED' if nonincumbents else 'UNKNOWN',
              'R3': 'SUPPORTED' if activity else 'UNKNOWN',
              'R4': 'SUPPORTED' if repeated else 'UNKNOWN',
              'R5_paid': case['own_paid'] if own_available else 'UNKNOWN',
              'R5_organic': case['own_organic'] if own_available else 'UNKNOWN'}
    # An established author's edition refutes a cold-start claim, not entry into an entire market.
    cold_start = 'SUPPORTED' if nonincumbents else 'CONTRADICTED' if eligible and all(
        w['creator'] in ('ESTABLISHED', 'DOMINANT') or w['release'] in ('NEW_EDITION', 'NEW_FORMAT') for w in eligible) else 'UNKNOWN'
    reason = 'INSUFFICIENT_EVIDENCE'
    decision = 'PARK'
    if case['demand'] == 'FAIL':
        reason = 'NEGATIVE_DEMAND'
    elif case['route_barrier'] == 'SUPPORTED':
        reason = 'OBSERVED_ENTRY_BARRIER'
    elif not eligible:
        reason = 'NO_SUPPORTED_ORGANIC_ROUTE'
    elif not research_witnesses:
        reason = 'ONLY_DOMINANT_OR_KNOWN_REISSUE_WITNESSES'
    elif not any(w in activity for w in research_witnesses):
        reason = 'NO_MATCHED_LISTING_ACTIVITY_PROXY'
    elif case['demand'] != 'PASS':
        reason = 'DEMAND_NOT_QUALIFIED'
    elif not case['history_reviewed']:
        reason = 'IDENTITY_HISTORY_NOT_REVIEWED'
    elif case['repeat_zero_prior'] and case['material_difference'] != 'SUPPORTED' and not (nonincumbents and activity):
        reason = 'PRIOR_REPEAT_REQUIRES_NEW_EVIDENCE'
    elif case['research_cap_minutes'] is None or not 0 < case['research_cap_minutes'] <= 20 or case['information_value'] not in ('MEDIUM', 'HIGH'):
        reason = 'RESEARCH_COST_OR_INFORMATION_VALUE_UNRESOLVED'
    else:
        decision, reason = 'PROMOTE_TO_GAP_ANALYSIS', 'BOUNDED_RESEARCH_OPTION_ONLY'
    return {'case_id': case['id'], 'policy_version': 'book-radar-reachability-policy/v2',
            'policy_status': 'PROPOSED_PENDING_OWNER_REVIEW', 'ladder': ladder,
            'cold_start_claim': cold_start, 'gap_recommendation': decision, 'reason': reason,
            'qualified_witness_ids': [w['id'] for w in eligible],
            'research_witness_ids': [w['id'] for w in research_witnesses],
            'commercial_activity_witness_ids': [w['id'] for w in activity],
            'entrant_activity_supported': bool(nonincumbents and any(w in activity for w in nonincumbents)),
            'sales_inferred': False, 'current_rating_velocity': 'UNKNOWN',
            'commercial_reachability_pass': False, 'production_authorized': False,
            'gap_collection_authorized': False, 'canonical_state_written': False}

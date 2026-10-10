"""Qualitative, read-only decision context over existing Radar records.

Semantic comparisons are explicitly evidenced review inputs, not title search,
numeric similarity, a new outcome store, or a replacement Wide decision.
"""
from copy import deepcopy
from datetime import date
from hashlib import sha256
from pathlib import Path

from .book_radar import load_state
from .book_radar_outcomes import UNKNOWN as U, outcome_report, evidence, _evidence_refs
from .book_radar_attribution import report as attribution_report
from .harness import ValidationError
from .schema_validation import load_draft_2020_12_validator

AXES = ('audience', 'job', 'discovery_route', 'query_family', 'marketplace',
        'language', 'product_type', 'market_mechanism', 'topic_domain', 'format',
        'freshness_event')
STATUSES = ('SAME', 'PARTIAL', 'DIFFERENT', U)
RELATIONSHIPS = ('NOVEL_MARKET', 'ADJACENT_TO_PRIOR_SUCCESS',
    'ADJACENT_TO_PRIOR_MIXED', 'ADJACENT_TO_PRIOR_ZERO_OR_NO_SIGNAL',
    'REPEAT_OF_EXISTING_EXPERIMENT', 'SAME_MARKET_DIFFERENT_PRODUCT_HYPOTHESIS', U)


def reference(root, path, selector):
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValidationError('Prior reference outside root or missing')
    return {'path': path, 'sha256': sha256(target.read_bytes()).hexdigest(), 'selector': selector}


def verify_reference(root, ref):
    if reference(root, ref['path'], ref['selector']) != ref:
        raise ValidationError('Prior evidence changed')


def paid_state(outcome):
    """Free downloads, KENP and royalties cannot become paid orders."""
    paid = outcome.get('paid_units', U)
    if paid == U:
        return 'UNKNOWN_PAID'
    if isinstance(paid, bool) or not isinstance(paid, (int, float)) or paid < 0:
        raise ValidationError('Invalid paid units')
    return 'POSITIVE_PAID' if paid > 0 else 'ZERO_PAID'


def assess_pair(comparison, outcome):
    if set(comparison) != set(AXES):
        raise ValidationError('All eleven comparison axes must be explicit')
    for axis in comparison.values():
        if axis['status'] not in STATUSES or not axis.get('reason'):
            raise ValidationError('Invalid comparison axis')
        if axis['status'] != U and (not axis.get('internal_evidence') or not axis.get('external_evidence')):
            raise ValidationError('Known comparison requires evidence from both sides')
    same = lambda key: comparison[key]['status'] == 'SAME'
    related = lambda key: comparison[key]['status'] in ('SAME', 'PARTIAL')
    incompatible = any(comparison[key]['status'] == 'DIFFERENT' for key in ('audience', 'job', 'marketplace', 'language'))
    # Domain/format alone never qualify. Job or audience plus a non-topic mechanism/route is essential.
    eligible = not incompatible and (related('job') or related('audience')) and any(
        related(k) for k in ('discovery_route', 'query_family', 'market_mechanism', 'freshness_event'))
    strong = eligible and all(same(k) for k in ('job', 'discovery_route', 'freshness_event', 'marketplace', 'language'))
    repeat = eligible and all(same(k) for k in ('job', 'freshness_event', 'product_type')) and related('query_family')
    pstate = paid_state(outcome)
    relationship = U
    if eligible:
        if repeat:
            relationship = 'REPEAT_OF_EXISTING_EXPERIMENT'
        elif same('job') and comparison['product_type']['status'] == 'DIFFERENT':
            relationship = 'SAME_MARKET_DIFFERENT_PRODUCT_HYPOTHESIS'
        else:
            relationship = 'ADJACENT_TO_PRIOR_SUCCESS' if pstate == 'POSITIVE_PAID' else 'ADJACENT_TO_PRIOR_ZERO_OR_NO_SIGNAL'
    return {'eligible_match': eligible, 'relationship': relationship,
            'match_confidence': 'HIGH' if strong else 'MEDIUM' if eligible else U,
            'paid_state': pstate, 'market_demand_verdict': U,
            'causal_mechanism': U, 'automatic_go': False, 'automatic_kill': False}


def decision_context(pairs, coverage, difference, external_status):
    if difference['state'] == 'VERIFIED' and not difference.get('evidence'):
        raise ValidationError('Verified material difference requires evidence')
    matched = [p for p in pairs if p['assessment']['eligible_match']]
    if not matched:
        relationship = 'NOVEL_MARKET' if coverage == 'SUFFICIENT' else U
        implication, priority = 'NORMAL_EXTERNAL_PIPELINE', 'NORMAL'
    else:
        classes = {p['assessment']['relationship'] for p in matched}
        states = {p['assessment']['paid_state'] for p in matched}
        if 'REPEAT_OF_EXISTING_EXPERIMENT' in classes:
            relationship = 'REPEAT_OF_EXISTING_EXPERIMENT'
        elif 'SAME_MARKET_DIFFERENT_PRODUCT_HYPOTHESIS' in classes:
            relationship = 'SAME_MARKET_DIFFERENT_PRODUCT_HYPOTHESIS'
        elif 'POSITIVE_PAID' in states and len(states) > 1:
            relationship = 'ADJACENT_TO_PRIOR_MIXED'
        else:
            relationship = next(iter(classes))
        negative = bool(states & {'ZERO_PAID', 'UNKNOWN_PAID'})
        if negative and difference['state'] != 'VERIFIED':
            implication, priority = 'PARK_CONTEXT_PENDING_MATERIAL_DIFFERENCE', 'LOW'
        else:
            implication, priority = 'OWNER_REVIEW_CONDITIONAL_INVESTIGATION', 'NORMAL'
    return {'relationship': relationship, 'implication': implication,
            'deep_research_priority': priority, 'external_status_preserved': external_status,
            'material_difference': deepcopy(difference), 'owner_asset_match': U,
            'owner_asset_status': 'NOT_ANALYZED', 'production_economics': U,
            'market_demand_verdict': U, 'mechanism_transfer': U,
            'automatic_go': False, 'automatic_kill': False,
            'requires_owner_review': True}


def internal_projection(root, as_of):
    """Read canonical actuals once; annotations never backfill historical hypotheses."""
    date.fromisoformat(as_of)
    if not (root / 'book-radar/state.json').is_file():
        raise ValidationError('Canonical Radar state is required')
    state_before = reference(root, 'book-radar/state.json', 'Radar canonical state')
    state = load_state(root)
    checked = {}
    for ref in _evidence_refs([state['observed_books'], state['actuals'], state['commercial_hypotheses'], state['calibrations']]):
        if ref['path'] not in checked:
            checked[ref['path']] = evidence(root, ref['path'])
        if checked[ref['path']] != ref:
            raise ValidationError('Canonical prior evidence hash mismatch')
    cards = attribution_report(root, 'cards', as_of)
    checkpoints = {c['book']['id']: c for c in outcome_report(root, 'checkpoints', as_of)['experiments']}
    card_by_book = {c['observation']['book_id']: c for c in cards['experiments']
                    if isinstance(c['observation'], dict) and c['status'] == 'HISTORICAL_PARTIAL'}
    result = {}
    for book in state['observed_books']:
        if book['publication_date'] != U and book['publication_date'] > as_of:
            continue
        rows = [a for a in state['actuals'] if a.get('schema_version') == 'book-radar-observed-actual/v1'
                and a['book_id'] == book['id'] and a['observed_date'] <= as_of]
        # Same-date conflicts cannot be silently selected by list order.
        latest = max((a['observed_date'] for a in rows), default=None)
        selected = [a for a in rows if a['observed_date'] == latest]
        if len(selected) > 1:
            raise ValidationError('Ambiguous latest internal actual')
        actual = selected[0] if selected else None
        card = card_by_book.get(book['id'])
        out = {'book_id': book['id'], 'experiment_id': card['id'] if card else U,
               'product_id': book['product_id'], 'radar_run_id': book['radar_run_id'],
               'title_for_identity_only': book['title'], 'publication_date': book['publication_date'],
               'first_verified_live_date': book['first_verified_live_date'],
               'formats': deepcopy(book['formats']), 'actual_id': actual['id'] if actual else U,
               'observed_date': actual['observed_date'] if actual else U,
               'actual_book_age_days': actual['book_age_days'] if actual else U,
               'marketplace_scope': actual['marketplace_scope'] if actual else U,
               'paid_units': actual['windows']['lifetime']['paid_units'] if actual else U,
               'free_units': actual['windows']['lifetime']['free_units'] if actual else U,
               'kenp': actual['windows']['kenp']['kenp_pages'] if actual else U,
               'royalties': actual['windows']['money']['estimated_royalties'] if actual else U,
               'currency': actual['windows']['money']['currency'] if actual else U,
               'windows': deepcopy(actual['windows']) if actual else U,
               'current_checkpoint': {'as_of': as_of, 'latest_actual_checkpoint': actual['checkpoint'] if actual else U,
                   'claim_checkpoint': deepcopy(card['observation']['checkpoint']) if card else U,
                   'due_unrecorded': [c['checkpoint'] for c in checkpoints.get(book['id'],{}).get('checkpoints',[])
                                      if c['collection_status']=='DUE_UNRECORDED'],
                   'next_due': deepcopy(checkpoints.get(book['id'],{}).get('next_due',U))},
               'checkpoint_schedule': deepcopy(checkpoints.get(book['id'],{}).get('checkpoints',U)),
               'discovery_observations': deepcopy(actual['discovery']) if actual else [],
               'attribution_state': deepcopy(card['attribution']) if card else {'classification': U},
               'calibration_state': [{k:c[k] for k in ('id','status','early_signal','model_update_authorized')}
                     for c in state['calibrations'] if c.get('book_id') == book['id'] and c.get('observed_date','9999') <= as_of],
               'data_completeness': {'actuals': 'AVAILABLE' if actual else U,
                   'observation_through': actual['observed_date'] if actual else U,
                   'as_of_is_not_a_new_KDP_capture': True, 'causal_attribution': 'INSUFFICIENT',
                   'market_specific_units': U, 'buyer_identity': U},
               'source_ref': reference(root,'book-radar/state.json',f"observed_books[id={book['id']}];actuals[id={actual['id'] if actual else U}]")}
        out['paid_state'] = paid_state(out)
        result[book['id']] = out
    if state_before != reference(root, 'book-radar/state.json', 'Radar canonical state'):
        raise ValidationError('Canonical state changed during prior projection')
    return result


def review(root, requests, as_of):
    catalog = internal_projection(root, as_of)
    reviews = []
    for request in requests:
        verify_reference(root, request['external_ref'])
        for ref in request['material_difference'].get('evidence', []):
            verify_reference(root, ref)
        pairs = []
        for candidate in request['comparisons']:
            bid = candidate['book_id']
            if bid not in catalog:
                raise ValidationError('Prior book is not in canonical observed catalog')
            for axis in candidate['axes'].values():
                for ref in axis['internal_evidence'] + axis['external_evidence']:
                    verify_reference(root, ref)
            internal = deepcopy(catalog[bid]);axes=deepcopy(candidate['axes'])
            pairs.append({'book_id': bid, 'comparison': axes, 'internal_outcome': internal,
                          'assessment': assess_pair(axes, internal)})
        context = decision_context(pairs, request['coverage'], request['material_difference'], request['external_status'])
        reviews.append({'opportunity_id': request['opportunity_id'], 'kind': request['kind'],
            'external_status': request['external_status'], 'external_ref': deepcopy(request['external_ref']),
            'internal_matches': [p for p in pairs if p['assessment']['eligible_match']],
            'rejected_comparisons': [p for p in pairs if not p['assessment']['eligible_match']],
            'coverage': {'state': request['coverage'], 'observed_catalog_books': len(catalog),
                         'scope_note': request['coverage_note'], 'all_portfolio_absence_proven': False},
            'context': context, 'value_of_information': request['value_of_information'],
            'next_research': deepcopy(request['next_research'])})
    value = {'schema_version': 'book-radar-portfolio-prior/v1', 'as_of': as_of,
             'canonical_source': reference(root,'book-radar/state.json','Radar canonical state'),
             'reviews': reviews, 'historical_state_written': False, 'wide_decisions_written': False,
             'scoring_changes': False, 'external_reads': 0, 'shelf_calls': 0, 'production_candidates': 0}
    validate(value)
    return value


def validate(value):
    schema = Path(__file__).resolve().parents[2] / 'schemas/BOOK_RADAR_PORTFOLIO_PRIOR_SCHEMA_V1.json'
    errors = list(load_draft_2020_12_validator(schema).iter_errors(value))
    if errors:
        raise ValidationError('Portfolio prior schema: '+errors[0].message)


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Read-only qualitative Radar portfolio prior context')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--requests', type=Path, required=True)
    parser.add_argument('--as-of', required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.root, json.loads(args.requests.read_text()), args.as_of), ensure_ascii=False, indent=2))

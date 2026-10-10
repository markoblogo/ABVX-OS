import copy
import shutil
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from abvx_harness.book_radar_shelf import check_snapshot, import_snapshot, report, compare

REAL = Path(__file__).resolve().parents[1]
FIXTURES = REAL / 'tests/fixtures/external-shelf-v1'

class ShelfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input'
        self.source.mkdir()
        (self.source / 'raw.txt').write_text('SYNTHETIC shelf evidence; no real products or market observations.\n')
        self.packet = json.loads((FIXTURES / 'distributed.json').read_text())
    def write(self):
        p = self.source / 'snapshot.json'
        p.write_text(json.dumps(self.packet, indent=2)+'\n')
        return p
    def test_valid_offline_import_idempotent(self):
        path = self.write()
        self.assertEqual(check_snapshot(path)['status'], 'PASS')
        self.assertEqual(import_snapshot(self.root, path)['added'], 1)
        self.assertEqual(import_snapshot(self.root, path)['added'], 0)
        self.assertFalse((self.root / 'book-radar/state.json').exists())

    def repeat(self):
        self.packet['id']='snapshot:repeat'
        self.packet['repeat_of']='snapshot:distributed'
        self.packet['observed_at']='2026-10-02T12:00:00Z'

    def test_unknown_slot_cannot_prove_exit_or_entry(self):
        self.packet['products'][0]['identity']['asin']={'state':'UNKNOWN','value':None,'evidence_ids':[]}
        import_snapshot(self.root,self.write())
        self.repeat()
        self.packet['products'][0]['identity']['asin']={'state':'OBSERVED','value':'X000000999','evidence_ids':['raw:1']}
        import_snapshot(self.root,self.write())
        result=compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][0]
        item=next(m for m in result['movement'] if m['identity_key'].endswith('X000000999'))
        self.assertEqual(item['status'],'UNKNOWN')

    def test_synthetic_record_cannot_be_reclassified_by_moving_folder(self):
        import_snapshot(self.root,self.write())
        base=self.root/'.tmp/external-shelf-intelligence-v1'
        shutil.copytree(base/'synthetic',base/'retained')
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):
            report(self.root,'cluster:distributed','RETAINED')

    def test_cli_check_and_invalid_option(self):
        import io
        from contextlib import redirect_stdout,redirect_stderr
        from abvx_harness.__main__ import main
        output=io.StringIO()
        with redirect_stdout(output):
            code=main(['book-radar','shelf','check',str(self.write()),'--json'],root=self.root)
        self.assertEqual(code,0)
        self.assertEqual(json.loads(output.getvalue())['status'],'PASS')
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(['book-radar','shelf','check',str(self.write()),'--live','yes'],root=self.root),1)

    def assert_invalid(self):
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):
            check_snapshot(self.write())

    def test_required_offline_scenarios_validate(self):
        for p in sorted(FIXTURES.glob('*.json')):
            with self.subTest(case=p.name):
                self.assertEqual(check_snapshot(p)['status'],'PASS')

    def test_asin_not_title_and_format_not_edition(self):
        self.packet=json.loads((FIXTURES/'same-title-different-asin.json').read_text())
        import_snapshot(self.root,self.write())
        row=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['counts']['unique_product_identities'],3)
        self.packet=json.loads((FIXTURES/'format-edition-ambiguity.json').read_text())
        import_snapshot(self.root,self.write())
        row=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['critical_missing_fields']['format'],2)
        self.assertEqual(row['critical_missing_fields']['edition'],2)
        self.assertEqual(row['counts']['unknown_identity_slots'],1)

    def test_unknown_is_not_zero(self):
        self.packet['products'][0]['review_count']={'state':'UNKNOWN','value':0,'evidence_ids':[]}
        self.assert_invalid()
        self.packet['products'][0]['review_count']={'state':'OBSERVED','value':0,'evidence_ids':['raw:1']}
        import_snapshot(self.root,self.write())
        row=report(self.root,'cluster:distributed','SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['review_counts']['minimum'],0)

    def test_absence_is_bounded_and_has_no_rank(self):
        self.packet['absences']=[{'identity_key':'asin:example.invalid:X000000999','presence':'NOT_FOUND_WITHIN_DEPTH_N','depth':3,'evidence_ids':['raw:1']}]
        check_snapshot(self.write())
        self.packet['absences'][0]['rank']=4
        self.assert_invalid()

    def test_organic_and_sponsored_are_separate(self):
        self.packet=json.loads((FIXTURES/'sponsored-heavy.json').read_text())
        import_snapshot(self.root,self.write())
        row=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['counts']['organic_slots'],1)
        self.assertEqual(row['counts']['sponsored_slots'],2)
        self.packet['products'][0]['position']['basis']={'state':'UNKNOWN','value':None,'evidence_ids':[]}
        self.assert_invalid()

    def test_bsr_not_sales_and_position_not_impressions(self):
        import_snapshot(self.root,self.write())
        result=report(self.root,'cluster:distributed','SYNTHETIC')
        forbidden={'sales','revenue','impressions','clicks','conversion','score','go','no_go'}
        def all_keys(v):
            if isinstance(v,dict):
                for k,x in v.items():
                    yield k
                    yield from all_keys(x)
            elif isinstance(v,list):
                for x in v:yield from all_keys(x)
        self.assertFalse(forbidden & set(all_keys(result)))
        self.packet['products'][0]['sales']=25
        self.assert_invalid()

    def test_observation_time_not_current_time(self):
        self.packet['products'][0]['publication_date']={'state':'OBSERVED','value':'2026-09-15','evidence_ids':['raw:1']}
        import_snapshot(self.root,self.write())
        r=report(self.root,'cluster:distributed','SYNTHETIC')['snapshots'][0]
        self.assertEqual(r['age_coverage']['publication_date']['age_days']['minimum'],16)
        self.assertEqual(report(self.root,'cluster:distributed','SYNTHETIC')['snapshots'][0],r)

    def test_context_drift_blocks_direct_comparison(self):
        import_snapshot(self.root,self.write())
        self.packet=json.loads((FIXTURES/'context-drift.json').read_text())
        import_snapshot(self.root,self.write())
        pair=compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][0]
        self.assertEqual(pair['comparability'],'BLOCKED')
        self.assertIn('CONTEXT_DRIFT:signed_in',pair['reasons'])
        self.assertEqual(pair['movement'],[])

    def test_every_context_dimension_is_checked(self):
        from abvx_harness.book_radar_shelf import compare_pair
        before=copy.deepcopy(self.packet)
        for key,v in before['context'].items():
            after=copy.deepcopy(before);after['repeat_of']=before['id'];after['id']='snapshot:repeat';after['observed_at']='2026-10-02T12:00:00Z'
            after['context'][key]=not v if isinstance(v,bool) else v+1 if isinstance(v,int) else v+['different'] if isinstance(v,list) else v+'-different'
            with self.subTest(field=key):
                self.assertEqual(compare_pair(before,after)['comparability'],'BLOCKED')

    def test_new_edition_not_cold_start_author(self):
        self.packet=json.loads((FIXTURES/'recent-entrants.json').read_text())
        import_snapshot(self.root,self.write())
        row=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['entrants']['recent_new_editions'],['slot:2'])
        self.assertEqual(row['entrants']['recent_new_titles'],['slot:1'])
        self.assertEqual(row['entrants']['evidence_backed_cold_start_authors'],['slot:1'])

    def test_missing_date_not_old_book(self):
        self.packet=json.loads((FIXTURES/'missing-ranks-dates.json').read_text())
        import_snapshot(self.root,self.write())
        row=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]
        self.assertEqual(row['age_coverage']['publication_date']['unknown'],3)
        self.assertIsNone(row['age_coverage']['publication_date']['age_days']['minimum'])
        self.assertEqual(row['entrants']['recent_new_titles'],[])

    def test_changed_input_evidence_fails_closed(self):
        path=self.write();import_snapshot(self.root,path)
        (self.source/'raw.txt').write_text('changed')
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):import_snapshot(self.root,path)

    def test_changed_same_id_bytes_fails_closed(self):
        path=self.write();import_snapshot(self.root,path)
        path.write_text(path.read_text()+' ')
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):import_snapshot(self.root,path)

    def test_changed_stored_evidence_fails_closed(self):
        import_snapshot(self.root,self.write())
        raw=next((self.root/'.tmp').glob('**/raw/*'));raw.chmod(0o644);raw.write_text('changed')
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):report(self.root,'cluster:distributed','SYNTHETIC')

    def test_report_is_readonly_and_t7_untouched(self):
        state=self.root/'book-radar/state.json';state.parent.mkdir();state.write_text('{"checkpoint_packets":[{"id":"T7","interpretation":"PROHIBITED_UNTIL_T14"}]}')
        import_snapshot(self.root,self.write())
        def hashes():return {str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        before=hashes();report(self.root,'cluster:distributed','SYNTHETIC');compare(self.root,'cluster:distributed','SYNTHETIC')
        self.assertEqual(hashes(),before)
        self.assertIn('PROHIBITED_UNTIL_T14',state.read_text())

    def test_synthetic_and_retained_are_separate(self):
        import_snapshot(self.root,self.write())
        self.assertEqual(report(self.root,'cluster:distributed','SYNTHETIC')['interop']['evidence'],[])
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):report(self.root,'cluster:distributed')
        self.packet['origin']='RETAINED'  # test-root only; models a separately retained packet
        import_snapshot(self.root,self.write())
        self.assertFalse(report(self.root,'cluster:distributed')['synthetic_only'])

    def test_existing_radar_evidence_interop(self):
        from abvx_harness.book_radar_outcomes import evidence
        self.packet['origin']='RETAINED'
        receipt=import_snapshot(self.root,self.write())
        self.assertEqual(evidence(self.root,receipt['evidence_ref']['path']),receipt['evidence_ref'])
        r=report(self.root,'cluster:distributed')
        for ref in r['interop']['evidence']:
            self.assertEqual(evidence(self.root,ref['path']),ref)
        for ref in r['snapshots'][0]['provenance']['stored_raw_evidence']:
            self.assertEqual(evidence(self.root,ref['path'])['sha256'],ref['sha256'])

    def test_partial_depth_blocks_comparison(self):
        self.packet=json.loads((FIXTURES/'partial-depth.json').read_text())
        import_snapshot(self.root,self.write())
        self.packet.update(id='snapshot:repeat',repeat_of='snapshot:partial-depth',observed_at='2026-10-02T12:00:00Z')
        import_snapshot(self.root,self.write())
        pair=compare(self.root,'cluster:partial-depth','SYNTHETIC')['pairs'][0]
        self.assertIn('PARTIAL_DEPTH',pair['reasons'])
        self.assertEqual(pair['movement'],[])

    def test_enter_exit_moves_stable_and_identity_change(self):
        import_snapshot(self.root,self.write());self.repeat()
        self.packet['products'][0]['position']['rank']['value']=2
        self.packet['products'][1]['position']['rank']['value']=1
        self.packet['products'][2]['identity']['asin']['value']='X000000004'
        import_snapshot(self.root,self.write())
        pair=compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][0]
        states={m['status'] for m in pair['movement']}
        self.assertEqual(states,{'MOVED_UP','MOVED_DOWN','ENTERED','EXITED_WITHIN_DEPTH'})
        exited=next(m for m in pair['movement'] if m['status']=='EXITED_WITHIN_DEPTH')
        self.assertIsNone(exited['after_rank']);self.assertEqual(exited['presence'],'NOT_FOUND_WITHIN_DEPTH_N')
        self.packet.update(id='snapshot:third',repeat_of='snapshot:repeat',observed_at='2026-10-03T12:00:00Z')
        self.packet['products'][2]['identity']['edition']['value']='2'
        import_snapshot(self.root,self.write())
        states={m['status'] for m in compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][-1]['movement']}
        self.assertEqual(states,{'STABLE','IDENTITY_CHANGED'})

    def test_repeat_missing_rank_is_unknown(self):
        import_snapshot(self.root,self.write());self.repeat()
        self.packet['products'][0]['position']['rank']={'state':'UNKNOWN','value':None,'evidence_ids':[]}
        import_snapshot(self.root,self.write())
        pair=compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][0]
        self.assertEqual(next(m for m in pair['movement'] if m['identity_key'].endswith('X000000001'))['status'],'UNKNOWN')

    def test_repeat_predecessor_required_and_frozen_cluster_immutable(self):
        self.repeat()
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):import_snapshot(self.root,self.write())
        self.packet['repeat_of']=None;import_snapshot(self.root,self.write())
        self.packet['id']='snapshot:new';self.packet['cluster']['label']='changed frozen definition'
        with self.assertRaises(ValidationError):import_snapshot(self.root,self.write())

    def test_source_evidence_escape_and_tamper_rejected(self):
        self.packet['evidence'][0]['path']='../raw.txt'
        self.assert_invalid()
        self.packet['evidence'][0]['path']=str((self.source/'raw.txt').resolve())
        self.assert_invalid()

    def test_measurements_require_evidence_and_isbn_checksum(self):
        self.packet['products'][0]['identity']['asin']['evidence_ids']=[]
        self.assert_invalid()
        self.packet['products'][0]['identity']['asin']['evidence_ids']=['not-there']
        self.assert_invalid()
        self.packet['products'][0]['identity']['asin']['evidence_ids']=['raw:1']
        self.packet['products'][0]['identity']['isbn']={'state':'OBSERVED','value':'9780306406158','evidence_ids':['raw:1']}
        self.assert_invalid()

    def test_timestamp_and_calendar_date_fail_closed(self):
        self.packet['observed_at']='2026-10-01T12:00:00'
        self.assert_invalid()
        self.packet['observed_at']='2026-10-01T12:00:00Z'
        self.packet['products'][0]['publication_date']['value']='2026-02-30'
        self.assert_invalid()

    def test_concentration_has_visible_scope_and_unknown_coverage(self):
        self.packet=json.loads((FIXTURES/'incumbent-dominated.json').read_text())
        import_snapshot(self.root,self.write())
        c=report(self.root,self.packet['cluster']['id'],'SYNTHETIC')['snapshots'][0]['concentration']['author']
        self.assertEqual(c['largest_share_all_slots'],1)
        self.assertEqual(c['unit'],'VISIBLE_CAPTURE_SLOT')
        self.assertEqual(c['unknown_slots'],0)

    def test_cli_import_report_compare_and_readonly_default(self):
        import io
        from contextlib import redirect_stdout,redirect_stderr
        from abvx_harness.__main__ import main
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(['book-radar','shelf','import',str(self.write()),'--json'],root=self.root),0)
            self.assertEqual(main(['book-radar','shelf','report','cluster:distributed','--origin','SYNTHETIC','--json'],root=self.root),0)
            self.assertEqual(main(['book-radar','shelf','compare','cluster:distributed','--origin','SYNTHETIC'],root=self.root),0)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(['book-radar','shelf','report','cluster:distributed'],root=self.root),1)

    def test_complete_depth_requires_all_slots_captured(self):
        self.packet['products']=self.packet['products'][:2]
        self.assert_invalid()

    def test_visible_rank_cannot_exceed_capture_depth(self):
        self.packet['products'][0]['position']['rank']['value']=99
        self.assert_invalid()

    def test_missing_context_blocks_comparison(self):
        import_snapshot(self.root,self.write());self.repeat()
        self.packet['context']['device']='UNKNOWN'
        import_snapshot(self.root,self.write())
        self.assertEqual(compare(self.root,'cluster:distributed','SYNTHETIC')['pairs'][0]['comparability'],'BLOCKED')

    def test_import_store_symlink_escape_rejected(self):
        base=self.root/'.tmp/external-shelf-intelligence-v1/synthetic'
        base.mkdir(parents=True)
        outside=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,outside)
        (base/'snapshots').symlink_to(outside,target_is_directory=True)
        from abvx_harness.harness import ValidationError
        with self.assertRaises(ValidationError):import_snapshot(self.root,self.write())
        self.assertEqual(list(outside.iterdir()),[])

if __name__ == '__main__':
    unittest.main()

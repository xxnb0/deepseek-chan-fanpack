import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.git', '.venv', 'output', '__pycache__'}


class ResearchTests(unittest.TestCase):
    def test_sources_have_unique_ids_urls_and_explicit_limits(self):
        registry = json.loads((ROOT / 'research/sources.json').read_text(encoding='utf-8'))
        entries = registry['sources']
        self.assertEqual(len(entries), 42)
        self.assertEqual(len({e['id'] for e in entries}), len(entries))
        self.assertEqual(len({e['url'] for e in entries}), len(entries))
        for entry in entries:
            with self.subTest(source=entry['id']):
                self.assertRegex(entry['id'], r'^[CFNT][0-9]{2}$')
                self.assertEqual(urlsplit(entry['url']).scheme, 'https')
                for field in ('kind','title','creator','access','origin_group','supports','limits'):
                    self.assertTrue(entry[field])
                if entry['access'].startswith('prior_'):
                    self.assertIsNone(entry['reviewed_at'])
                else:
                    self.assertIn(entry['access'], {'page_text','search_excerpt'})
                    self.assertEqual(entry['reviewed_at'], registry['as_of'])
        for field in ('downloaded_media','full_video_watched','transcript_extracted'):
            self.assertFalse(registry['defaults'][field])

    def test_catalog_source_references_resolve(self):
        entries = json.loads((ROOT / 'research/sources.json').read_text(encoding='utf-8'))['sources']
        ids = {entry['id'] for entry in entries}
        for name in ('docs/meme-catalog.md','docs/community-sources.md'):
            used = set(re.findall(r'\b[CFNT][0-9]{2}\b', (ROOT / name).read_text(encoding='utf-8')))
            self.assertTrue(used <= ids, used - ids)
        profile = json.loads((ROOT / 'assets/pet/atlas-profile.json').read_text(encoding='utf-8'))
        self.assertIn(profile['source_id'], ids)
        self.assertIn(profile['community_11row_variant']['source_id'], ids)

    def test_recovered_tts_probe_is_not_current_runtime_or_voice_proof(self):
        probe = json.loads((ROOT / 'research/muse-tts-probe.json').read_text(encoding='utf-8'))
        self.assertEqual(probe['evidence_kind'], 'recovered_persisted_cloud_task')
        self.assertFalse(probe['rerun_in_current_turn'])
        self.assertEqual(probe['root_cause_of_initial_failures'], 'unknown')
        for field in ('native_voice_modified','subjective_audition_verified',
                      'realtime_voice_replacement_verified','message_delivery_verified'):
            self.assertFalse(probe[field])

    def test_manifest_covers_all_materialized_source_files(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        listed = {entry['path'] for entry in manifest['files']}
        sources = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*')
                   if p.is_file() and p.name != 'manifest.json'
                   and p.suffix != '.pyc'
                   and not any(part in IGNORED for part in p.relative_to(ROOT).parts)}
        self.assertTrue(sources <= listed, sorted(sources - listed))

    def test_runtime_dependency_files_are_not_packaged(self):
        entries = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['files']
        for entry in entries:
            path = Path(entry['path'])
            self.assertFalse(any(part in IGNORED for part in path.parts))
            self.assertFalse((ROOT / path).is_symlink())
            self.assertNotIn(path.name, {'.env','hosts.yml'})

    def test_new_persona_cases_remain_manual_acceptance(self):
        cases = json.loads((ROOT / 'tests/persona-cases.json').read_text(encoding='utf-8'))
        self.assertEqual(cases['purpose'], 'manual_host_behavior_acceptance_not_an_automated_model_eval')
        ids = {case['id'] for case in cases['cases']}
        self.assertTrue({'daily_curiosity','joke_not_reciprocated','fantasy_branch',
                         'native_voice_vs_audio','pet_contract_mismatch','no_fake_shared_past'} <= ids)


if __name__ == '__main__':
    unittest.main()

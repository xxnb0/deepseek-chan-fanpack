import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ContractTests(unittest.TestCase):
    def test_persona_entries_agree(self):
        persona=json.loads((ROOT/'personality.json').read_text())
        soul=(ROOT/'SOUL.md').read_text().split('---',2)[2].strip()
        self.assertEqual(persona['body'].strip(),soul)
        self.assertTrue((ROOT/'prompts/system.md').read_text().strip().endswith(soul))
        self.assertEqual(persona['name'],'鲸鱼娘（大肥鱼）')

    def test_ai_first_entry(self):
        start=(ROOT/'START_HERE.md').read_text()
        self.assertIn('当前会话',start)
        self.assertIn('不要求 SOUL.md',start)
        self.assertNotIn('pip install',start)
        self.assertNotIn('scripts/install.py',(ROOT/'README.md').read_text())
        self.assertIn('START_HERE.md',(ROOT/'README.md').read_text())

    def test_active_docs_do_not_assume_repository_visibility(self):
        for p in list(ROOT.rglob('*.md'))+[ROOT/'personality.json']:
            if 'sources' in p.relative_to(ROOT).parts or p.name=='validation-v1.0.0.md':continue
            text=p.read_text().lower()
            for term in ('私仓','私有角色资料包','私有备份','private repository'):
                self.assertNotIn(term,text,str(p.relative_to(ROOT)))
        self.assertIn('需要能读取仓库与所用资源',(ROOT/'README.md').read_text())

    def test_examples_are_manual_not_claimed_live_evaluation(self):
        cases=json.loads((ROOT/'tests/persona-cases.json').read_text())
        self.assertEqual(cases['purpose'],'manual_host_behavior_acceptance_not_an_automated_model_eval')
        ids={c['id'] for c in cases['cases']}
        self.assertEqual(len(ids),len(cases['cases']))
        self.assertTrue({'serious','correction','session_only','multi_turn','no_media','voice_fallback'}<=ids)
        for c in cases['cases']:
            for field in ('prompt','context','expected','avoid','media'):
                self.assertTrue(c[field])

    def test_all_asset_metadata_agrees(self):
        manifest=json.loads((ROOT/'manifest.json').read_text())
        files={x['path']:x for x in manifest['files']}
        index=json.loads((ROOT/'assets/stickers/common/index.json').read_text())
        variants=json.loads((ROOT/'assets/stickers/common/variants.json').read_text())
        self.assertEqual(len(index),33)
        self.assertEqual(len(variants),33)
        self.assertEqual(sum(x['background']=='transparent' for x in variants),21)
        for item in index:
            m=files['assets/stickers/common/'+item['file']]
            self.assertEqual(m['sha256'],item['sha256'])
            if 'bytes' in item:self.assertEqual(m['bytes'],item['bytes'])
        archive=json.loads((ROOT/'archive/reference-library/index.json').read_text())
        self.assertEqual(len(archive),518)
        self.assertFalse(manifest['archive']['runtime_enabled'])

if __name__=='__main__':unittest.main()

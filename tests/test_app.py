import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def button(app, label):
    return next(w for w in app.button if w.label == label)


def select(app, label):
    return next(w for w in app.selectbox if w.label == label)


class AppChecks(unittest.TestCase):
    def test_search_edit_recovery_and_export(self):
        app = AppTest.from_file(str(ROOT / 'app.py')).run()
        button(app, 'Start review').click().run()
        self.assertTrue(app.error)
        button(app, 'Load six examples').click().run()
        button(app, 'Start review').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['claims'][0]['search'][0]['id'], 'A-R03')
        self.assertFalse(any(b.label == 'Show demo reference' for b in app.button))
        button(app, 'Save my judgment').click().run()
        self.assertTrue(app.error)
        app.radio[0].set_value('Supported')
        button(app, 'Save my judgment').click().run()
        button(app, 'Show demo reference').click().run()
        self.assertTrue(app.session_state['claims'][0]['revealed'])
        button(app, 'Undo last save').click().run()
        self.assertIsNone(app.session_state['claims'][0]['judgment'])
        # Editing triggers a new search and clears both judgment and preset analysis.
        next(t for t in app.text_area if t.label == 'Claim text').set_value('A 5-5-5 schedule uses five days between tests.')
        button(app, 'Save changes').click().run()
        claim = app.session_state['claims'][0]
        self.assertEqual(claim['search'][0]['id'], 'B-U02')
        self.assertIsNone(claim['judgment'])
        self.assertFalse(claim['revealed'])
        self.assertFalse(any(b.label == 'Show demo reference' for b in app.button))
        # A new unrelated claim produces a search failure without deciding a verdict.
        next(t for t in app.text_area if t.label == 'Claim text').set_value('Quantum entanglement determines black hole temperature.')
        button(app, 'Save changes').click().run()
        self.assertEqual(app.session_state['claims'][0]['search'], [])
        self.assertIsNone(app.radio[0].value)
        self.assertEqual(select(app, 'Choose a source passage').value, '')
        self.assertTrue(app.warning)
        app.checkbox[0].check().run()
        self.assertEqual(len(select(app, 'Choose a source passage').options), 14)
        # Manual override of retrieval is possible; deliberately save without a passage.
        select(app, 'Choose a source passage').set_value('').run()
        app.radio[0].set_value('Insufficient evidence')
        button(app, 'Save my judgment').click().run()
        button(app, 'View all records').click().run()
        with patch('streamlit.download_button') as download:
            app.run()
            payload = json.loads(download.call_args.args[1])
        self.assertEqual(payload['mode'], 'local_retrieval_no_api')
        self.assertEqual(payload['records'][0]['retrieval']['candidates'], [])
        self.assertEqual(payload['records'][0]['user_judgment']['evidence_id'], '')
        self.assertIsNone(payload['records'][0]['viewed_demo_reference'])
        self.assertFalse(app.exception)
        for path in [ROOT / 'app.py', ROOT / 'retrieval.py', ROOT / 'data/corpus.json', ROOT / 'data/demo.json']:
            self.assertFalse(any('\u4e00' <= c <= '\u9fff' for c in path.read_text()), str(path))


if __name__ == '__main__':
    unittest.main()

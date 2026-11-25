import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from retrieval import retrieve

CORPUS = json.loads((ROOT / 'data/corpus.json').read_text())


class RetrievalChecks(unittest.TestCase):
    def test_time_and_schedule_queries_find_different_evidence(self):
        delayed = retrieve('One week later students recalled more than after restudying.', CORPUS)
        immediate = retrieve('After five minutes restudying produced better recall.', CORPUS)
        units = retrieve('The 5-5-5 schedule means reviewing every five days.', CORPUS)
        self.assertEqual(delayed[0]['id'], 'A-R03')
        self.assertEqual(immediate[0]['id'], 'A-R01')
        self.assertEqual(units[0]['id'], 'B-U02')

    def test_empty_unrelated_and_date_only_queries_return_no_candidates(self):
        for query in ['', 'the and of', '2011 2006', 'Quantum entanglement determines black hole temperature.']:
            with self.subTest(query=query):
                self.assertEqual(retrieve(query, CORPUS), [])

    def test_negation_is_not_a_support_judgment(self):
        a = retrieve('Spacing between repeated tests enhanced retention.', CORPUS)
        b = retrieve('Spacing between repeated tests did not enhance retention.', CORPUS)
        self.assertTrue(a and b)
        self.assertEqual(a[0]['id'], b[0]['id'])
        self.assertNotIn('verdict', a[0])

    def test_authored_explanations_cannot_influence_ranking(self):
        changed = copy.deepcopy(CORPUS)
        for p in changed['passages']:
            p['context'] = 'Quantum entanglement determines black hole temperature.'
        self.assertEqual(retrieve('Quantum entanglement determines black hole temperature.', changed), [])

    def test_candidates_are_real_sorted_and_bounded(self):
        result = retrieve('Students recalled material after tests with different spacing intervals.', CORPUS)
        self.assertLessEqual(len(result), 3)
        self.assertEqual([r['score'] for r in result], sorted([r['score'] for r in result], reverse=True))
        valid = {p['id'] for p in CORPUS['passages']}
        self.assertTrue(all(r['id'] in valid and len(r['matched_terms']) >= 2 for r in result))
        self.assertEqual(result, retrieve('Students recalled material after tests with different spacing intervals.', CORPUS))


if __name__ == '__main__':
    unittest.main()

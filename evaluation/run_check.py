"""Reproduce the documented first-use retrieval check without changing the model."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from retrieval import METHOD, MIN_SCORE, retrieve


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    corpus = json.loads((ROOT / 'data/corpus.json').read_text())
    path = Path(__file__).with_name('cases.json')
    batch = json.loads(path.read_text())
    ids = {p['id'] for p in corpus['passages']}
    assert all(set(case['expected_ids']) <= ids for case in batch['cases'])
    code_hash = digest(ROOT / 'retrieval.py')
    results = []
    for case in batch['cases']:
        candidates = retrieve(case['claim'], corpus)
        returned = [item['id'] for item in candidates]
        expected = set(case['expected_ids'])
        results.append({**case, 'candidates': candidates,
                        'expected_passage_in_top3': bool(expected & set(returned)) if expected else None,
                        'expected_passage_at_rank1': returned[0] in expected if returned and expected else (False if expected else None)})
    covered = [r for r in results if r['type'] == 'covered']
    unsupported = [r for r in results if r['type'] != 'covered']
    assert digest(ROOT / 'retrieval.py') == code_hash
    report = {
        'run_at_utc': datetime.now(timezone.utc).isoformat(),
        'method': METHOD, 'min_score': MIN_SCORE, 'limit': 3, 'min_shared_nonnumeric_terms': 2,
        'retrieval_sha256': code_hash, 'corpus_sha256': digest(ROOT / 'data/corpus.json'),
        'cases_sha256': digest(path), 'case_design': batch['authorship'],
        'metrics': {'covered_cases': len(covered),
                    'top3_hits': sum(r['expected_passage_in_top3'] for r in covered),
                    'rank1_hits': sum(r['expected_passage_at_rank1'] for r in covered),
                    'unsupported_or_outside_cases': len(unsupported),
                    'unsupported_or_outside_returning_candidates': sum(bool(r['candidates']) for r in unsupported)},
        'interpretation': 'Expected-passage retrieval only. Not factual-judgment accuracy, participant behaviour or evidence of learning benefit. Expected IDs were not independently annotated.',
        'results': results}
    Path(__file__).with_name('results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['metrics']))
    for result in results:
        print(result['id'], [r['id'] for r in result['candidates']], result['expected_passage_in_top3'])


if __name__ == '__main__':
    main()

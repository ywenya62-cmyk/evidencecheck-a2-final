"""Local lexical retrieval over source text and bibliographic metadata only."""
import math
import re
import unicodedata
from collections import Counter

STOP_WORDS = set('''a an and are as at be been being but by can could did do does for from
had has have how i if in into is it its may more most my no not of on only or our
so than that the their them then there these they this those to was we were what
when where which who will with would you your means found find paper study studies
experiment experiments'''.split())
NORMALISE = {
    'one': '1', 'two': '2', 'three': '3', 'five': '5',
    'minute': 'min', 'minutes': 'min', 'mins': 'min',
    'weeks': 'week', 'days': 'day', 'trials': 'trial',
    'students': 'student', 'undergraduates': 'student',
    'tests': 'test', 'tested': 'test', 'testing': 'test',
    'restudied': 'restudy', 'restudying': 'restudy',
    'recalled': 'recall', 'recalling': 'recall',
    'intervals': 'interval', 'schedules': 'schedule',
    'retrieval': 'recall', 'benefits': 'benefit', 'benefited': 'benefit',
}
METHOD = 'tfidf_cosine_v1'
MIN_SCORE = 0.08


def tokens(text):
    text = unicodedata.normalize('NFKC', text).lower().replace('–', '-').replace('—', '-')
    words = re.findall(r'\d+(?:-\d+)+|[a-z]+|\d+', text)
    return [NORMALISE.get(word, word) for word in words if word not in STOP_WORDS]


def retrieve(query, corpus, limit=3):
    """Return candidates, never a support verdict or calibrated confidence."""
    passages = corpus['passages']
    docs = []
    for passage in passages:
        paper = corpus['papers'][passage['paper']]
        # Authored explanations and demo verdicts must not affect ranking.
        text = ' '.join([passage['quote'], passage['title'], passage['section'],
                         paper['authors'], str(paper['year'])])
        docs.append(Counter(tokens(text)))
    query_terms = Counter(tokens(query))
    if not query_terms or not docs:
        return []
    vocabulary = set().union(*(set(doc) for doc in docs))
    idf = {word: math.log((1 + len(docs)) / (1 + sum(word in doc for doc in docs))) + 1
           for word in vocabulary | set(query_terms)}

    def vector(counts):
        return {word: (1 + math.log(count)) * idf[word] for word, count in counts.items()}

    q = vector(query_terms)
    qnorm = math.sqrt(sum(value * value for value in q.values()))
    results = []
    for passage, counts in zip(passages, docs):
        shared = sorted(set(counts) & set(query_terms))
        content = [term for term in shared if not term.isdigit()]
        # Two shared nonnumeric terms reduce date-only and incidental matches.
        if len(content) < 2:
            continue
        doc = vector(counts)
        norm = math.sqrt(sum(value * value for value in doc.values()))
        score = sum(q[term] * doc[term] for term in shared) / (qnorm * norm)
        if score >= MIN_SCORE:
            results.append({'id': passage['id'], 'score': round(score, 6), 'matched_terms': shared})
    return sorted(results, key=lambda result: (-result['score'], result['id']))[:limit]

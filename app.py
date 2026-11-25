import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from retrieval import METHOD, MIN_SCORE, retrieve

DATA = json.loads((Path(__file__).parent / 'data' / 'demo.json').read_text())
CORPUS = json.loads((Path(__file__).parent / 'data' / 'corpus.json').read_text())
DATA['papers'] = CORPUS['papers']
DATA['evidence'] = {passage['id']: passage for passage in CORPUS['passages']}
CASES = {case['claim']: case for case in DATA['cases']}
LABELS = ['Supported', 'Partially supported', 'Contradicted', 'Insufficient evidence']
SAMPLE = '\n'.join(case['claim'] for case in DATA['cases'])

st.set_page_config(page_title='EvidenceCheck · Study Advice Verification', page_icon='📖', layout='wide')
st.markdown('''<style>
.block-container {max-width: 1180px; padding-top: 2.5rem;}
.stApp {background: #f7f9fc;}
h1,h2,h3 {color: #182c49;}
[data-testid="stMetric"] {background: white; border: 1px solid #dde5ef; border-radius: 10px; padding: 16px;}
</style>''', unsafe_allow_html=True)


def go(step):
    st.session_state.step = step


def load_sample():
    st.session_state.answer = SAMPLE


def new_claim(text):
    return {'text': text, 'judgment': None, 'history': [], 'revealed': False,
            'search': retrieve(text, CORPUS)}


def evidence_name(eid):
    e = DATA['evidence'][eid]
    p = DATA['papers'][e['paper']]
    return f"{p['authors']} ({p['year']}) · PDF page {e['page']} · {e['section']}"


def show_evidence(eid):
    e = DATA['evidence'][eid]
    p = DATA['papers'][e['paper']]
    st.markdown(f"**{p['authors']} ({p['year']})**")
    st.caption(f"Passage {eid} · PDF page {e['page']} / journal page {e['printed_page']} · {e['section']}")
    st.markdown('**Source excerpt**')
    st.info(e['quote'])
    st.link_button('Open source page', f"{p['url']}#page={e['page']}")
    with st.expander('Context summary'):
        st.write(e['context'])
        st.caption('This is a project-written summary. Open the source above to read the full context.')


for key, value in {'step': 1, 'claims': [], 'revision': 0}.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title('EvidenceCheck')
st.write('Retrieval practice and spacing · Does the evidence support the advice?')
st.info('Local prototype: candidate passages are ranked from your claim text. No API or generative model is used. A retrieved passage may support, contradict or be irrelevant to the claim.')

with st.sidebar:
    st.subheader('Source scope')
    st.write('This prototype uses only these two studies:')
    for paper in DATA['papers'].values():
        st.markdown(f"**{paper['authors']} ({paper['year']})**")
        st.caption(paper['title'])
        st.link_button('Read paper', paper['url'])
    st.divider()
    st.caption('Judgment guide')
    st.write('Supported: the source supports the claim within its stated scope.\n\nPartially supported: only part of the claim has support.\n\nContradicted: the claim conflicts with the source.\n\nInsufficient evidence: these sources do not settle the claim.')
    st.caption('Records are kept only in this session and may be lost on refresh or disconnection. Export to keep a copy. No text is sent to an AI service.')

with st.expander('Browse evidence library'):
    st.write(f"{len(CORPUS['passages'])} curated passages from two studies. These excerpts do not cover everything in the full papers.")
    st.caption('Passage IDs are assigned by this project. Page locations and excerpts have been checked against the source PDFs; this does not establish that a passage supports a particular claim.')
    library_id = st.selectbox('Browse a passage', list(DATA['evidence']),
                               format_func=lambda eid: f"{eid} · {DATA['evidence'][eid]['title']}")
    show_evidence(library_id)
    st.download_button('Download evidence library (JSON)', json.dumps(CORPUS, ensure_ascii=False, indent=2),
                       file_name='evidencecheck-corpus.json', mime='application/json')

nav = st.columns(3)
for i, label in enumerate(['1 · Prepare claims', '2 · Review evidence', '3 · Review record'], 1):
    nav[i-1].button(label, on_click=go, args=(i,), width='stretch',
                    type='primary' if st.session_state.step == i else 'secondary',
                    disabled=i > 1 and not st.session_state.claims)

claims = st.session_state.claims
rev = st.session_state.revision
if st.session_state.step == 1:
    st.subheader('Prepare your claims')
    st.write('Load the six examples or enter your own text. Put one claim on each line; edit, remove or add claims before continuing.')
    st.button('Load six examples', on_click=load_sample)
    with st.form('input'):
        text = st.text_area('Claims to review (one per line)', key='answer', height=270,
                            placeholder='Enter claims here, or load the examples above.')
        st.caption('One line becomes one claim. Local text matching finds candidate passages; it does not decide whether a claim is true. Starting again replaces all existing review records.')
        submitted = st.form_submit_button('Start review', type='primary')
    if submitted:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            st.error('Enter at least one claim or load the examples first.')
        else:
            st.session_state.claims = [
                new_claim(line)
                for line in lines
            ]
            st.session_state.revision += 1
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    done = sum(c['judgment'] is not None for c in claims)
    st.progress(done / len(claims), text=f'{done} of {len(claims)} judgments recorded')
    index = st.selectbox('Select a claim', range(len(claims)),
                         format_func=lambda i: f"{i+1}. {claims[i]['text'][:48]}", key=f'index_{rev}')
    claim = claims[index]
    if 'search' not in claim:
        claim['search'] = retrieve(claim['text'], CORPUS)
    prefix = f'{rev}_{index}'
    case = CASES.get(claim['text'])
    left, right = st.columns([1, 1], gap='large')
    with left:
        st.subheader(f'Claim {index+1} of {len(claims)}')
        st.write(claim['text'])
        with st.expander('Edit this claim'):
            with st.form(f'edit_{prefix}'):
                edited = st.text_area('Claim text', value=claim['text'], key=f'edit_text_{prefix}')
                edit = st.form_submit_button('Save changes')
            if edit:
                if not edited.strip():
                    st.error('The claim cannot be empty.')
                elif edited.strip() != claim['text']:
                    claim['text'] = edited.strip()
                    claim['judgment'] = None
                    claim['history'] = []
                    claim['revealed'] = False
                    claim['search'] = retrieve(claim['text'], CORPUS)
                    # New widget keys prevent old choices surviving a changed claim.
                    st.session_state.revision += 1
                    st.rerun()
        if case:
            st.caption(f"Example {case['id']} · A preset reference is available after you save a judgment")
        else:
            st.info('Custom claim: candidates are found locally. There is no preset reference judgment for this wording.')
        st.write('Compare the source evidence before recording your judgment.')
    with right:
        st.subheader('Candidate evidence')
        candidates = claim['search']
        suggested = [result['id'] for result in candidates]
        st.caption('Ranked by shared words and text similarity, not factual support. Negation and meaning are not verified.')
        if not candidates:
            st.warning('No candidate met the word-matching filter. This is a search limitation, not proof that the full papers contain no relevant evidence.')
        with st.expander('How were these passages selected?'):
            st.write('The search compares your claim with source excerpts, headings and bibliographic metadata. Common words are ignored and a small set of word forms and number words is normalised.')
            st.write('Up to three passages are returned, requiring two shared nonnumeric terms and a cosine similarity of at least 0.08. This filter has not been calibrated for relevance or correctness.')
            if candidates:
                st.table([{'Rank': n, 'Passage': item['id'], 'Matched terms': ', '.join(item['matched_terms'])}
                          for n, item in enumerate(candidates, 1)])
        browse_all = st.checkbox('Browse all passages instead', key=f'browse_{prefix}')
        options = [''] + (list(DATA['evidence']) if browse_all else suggested)
        eid = st.selectbox('Choose a source passage', options,
                           index=1 if len(options) > 1 else 0,
                           format_func=lambda e: evidence_name(e) if e else 'No passage selected',
                           key=f'evidence_{prefix}_{browse_all}')
        if eid:
            show_evidence(eid)
            match = next((item for item in candidates if item['id'] == eid), None)
            if match:
                st.caption('Matched terms (normalised): ' + ', '.join(match['matched_terms']))
        else:
            st.caption('You can browse all 13 passages or open the full papers. No selected passage does not mean the claim is false.')
    st.divider()
    current = claim['judgment']
    with st.form(f'judge_{prefix}'):
        verdict = st.radio('My judgment', LABELS, index=None, horizontal=True, key=f'verdict_{prefix}')
        reason = st.text_area('My reason (optional)', key=f'reason_{prefix}', height=85)
        save = st.form_submit_button('Save my judgment', type='primary')
    if save:
        if verdict is None:
            st.error('Choose a judgment before saving.')
        else:
            claim['history'].append(copy.deepcopy(current))
            claim['judgment'] = {'verdict': verdict, 'reason': reason, 'evidence_id': eid,
                                  'saved_at': datetime.now(timezone.utc).isoformat(),
                                  'retrieval': {'method': METHOD, 'candidates': copy.deepcopy(claim['search'])}}
            st.success('Your judgment is saved. You can revise it or undo the last save.')
    current = claim['judgment']
    if current:
        st.write(f"Saved judgment: **{current['verdict']}**")
        if st.button('Undo last save', key=f'undo_{prefix}', disabled=not claim['history']):
            claim['judgment'] = claim['history'].pop()
            for key in [f'verdict_{prefix}', f'reason_{prefix}']:
                del st.session_state[key]
            st.rerun()
        if case:
            if st.button('Show demo reference', key=f'show_{prefix}'):
                claim['revealed'] = True
            if claim['revealed']:
                with st.container(border=True):
                    st.markdown(f"**Preset reference judgment: {case['verdict']}**")
                    st.write(case['reason'])
                    st.caption('This explanation was prepared for the original case using the relevant evidence. It is not live AI analysis and does not change your judgment.')
                    for ref in case['evidence']:
                        st.caption(evidence_name(ref))
        else:
            st.caption('Edited claims do not inherit the reference judgment for the original case.')
    st.button('View all records', on_click=go, args=(3,))

elif st.session_state.step == 3:
    st.subheader('Review record')
    st.write('Your judgments and viewed demo references are recorded separately. These examples do not establish general system accuracy.')
    rows, records = [], []
    for i, claim in enumerate(claims, 1):
        result = claim['judgment']
        case = CASES.get(claim['text'])
        ref = case if claim['revealed'] else None
        eid = result['evidence_id'] if result else ''
        rows.append({'No.': i, 'Claim': claim['text'], 'My judgment': result['verdict'] if result else 'Not reviewed',
                     'My reason': result['reason'] if result else '',
                     'Source location': evidence_name(eid) if eid else 'Not selected',
                     'Viewed preset reference': ref['verdict'] if ref else 'Not viewed / not applicable'})
        records.append({'claim': claim['text'], 'user_judgment': result,
                        'retrieval': {'method': METHOD, 'candidates': claim.get('search', [])},
                        'viewed_demo_reference': {'verdict': ref['verdict'], 'reason': ref['reason']} if ref else None})
    st.dataframe(rows, hide_index=True, width='stretch')
    payload = {'mode': 'local_retrieval_no_api',
               'retrieval_settings': {'method': METHOD, 'min_score': MIN_SCORE, 'min_shared_terms': 2, 'limit': 3}, 'exported_at': datetime.now(timezone.utc).isoformat(),
               'sources': DATA['papers'], 'corpus_version': CORPUS['version'], 'evidence_catalog': DATA['evidence'], 'records': records}
    st.download_button('Export review record (JSON)', json.dumps(payload, ensure_ascii=False, indent=2),
                       file_name='evidencecheck-record.json', mime='application/json')
    st.caption('The export includes selected evidence, your judgments and reasons, and any preset reference explanations you have viewed.')
    st.button('Back to evidence review', on_click=go, args=(2,))

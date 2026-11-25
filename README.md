# EvidenceCheck

Prose word count: 939 (whitespace-separated prose words; excluding headings, bibliography entries, fenced commands, list markers, link destinations and this line; hyphenated terms counted as one word).

Retrieval practice and spacing: does the evidence support AI-generated study advice? An English-language local prototype for Assignment 2.

## Project status

Implemented: line-based claim preparation, local evidence retrieval for arbitrary English claims, source browsing, side-by-side comparison, editing and automatic re-search, saving and undoing judgments, and JSON export. The app runs locally without an API key, paid service, database or model download. Source links require internet access.

Simulated: reference explanations for six authored examples remain preset. These cases intentionally include supported, partially supported, contradicted and insufficient-evidence claims; they are not participant data or recorded AI outputs. References appear only after a user saves a judgment and only for an exact match to an original example. They do not determine retrieval rankings.

The system does not generate text, automatically extract claims or decide factual support. Users judge whether candidate evidence supports or contradicts a claim. Records exist only in the current session and may be lost on refresh or disconnection; export to keep a copy.

## Technology and setup

Python 3.12, Streamlit 1.67.0, JSON and Python standard-library text processing. No additional retrieval dependencies are needed.

From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the printed local URL. Press Control+C to stop. Use the original English page rather than browser translation, which can change interface wording and source excerpts.

## Walkthrough

1. Optionally inspect “Browse evidence library”. Load six examples or enter one claim per line, then start review.
2. Select a claim. Inspect ranked passages, their source locations and matched words. Open the paper for full context.
3. If candidates are missing or irrelevant, select “Browse all passages instead”. A search failure does not mean the papers contain no answer.
4. Save a judgment and optional reason. For original examples, optionally reveal the preset reference. Revise or undo your judgment.
5. Edit a claim to trigger a new search, or view all records and export JSON.

Editing clears the changed claim’s saved judgment, undo history and reference disclosure. Starting claim preparation again replaces all records. Changing the passage being read does not alter an existing saved judgment until saved again. Exports preserve candidate rankings, matched terms, retrieval settings, selected evidence and user judgments. Similarity scores are not confidence probabilities.

## Retrieval method and limitations

`retrieval.py` computes TF-IDF cosine similarity over source excerpts, headings and author/year metadata. It excludes project-written context summaries and all reference judgments. A small explicit vocabulary map normalises word forms, number words and the domain terms retrieval/recall. Common words are removed.

Up to three candidates are returned, requiring two shared nonnumeric terms and similarity of at least 0.08. This heuristic is not calibrated for relevance. It can miss paraphrases, cannot interpret negation or resolve entailment, and may rank irrelevant passages sharing general words. For example, the study-break claim retrieves participant descriptions because of “university students”; those descriptions do not support the proposed schedule. Users must inspect the passage and can override the ranking. Only 13 excerpts are indexed, so coverage is limited.

## Sources and data

- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. Psychological Science, 17(3), 249–255. https://doi.org/10.1111/j.1467-9280.2006.01693.x
- Karpicke, J. D., & Bauernschmidt, A. (2011). Spaced retrieval: Absolute spacing enhances learning regardless of relative spacing. Journal of Experimental Psychology: Learning, Memory, and Cognition, 37(5), 1250–1257. https://doi.org/10.1037/a0023436

`data/corpus.json` contains 13 page-verified excerpts, metadata, section headings, project-written summaries and source fingerprints. Passage IDs are assigned by this project. PDF line breaks and word wrapping are normalised; consult linked pages for full context. Full papers are not bundled and no licence to third-party material is granted. `data/demo.json` separately stores examples and preset judgments. Authentic quotations do not automatically establish semantic support.

## Development record and checks

- Built the three-stage interaction and recovery controls; translated all supplied content into English.
- Replaced duplicated evidence with a single corpus and checked its excerpts against source pages.
- Added deterministic local retrieval after deciding to avoid paid API access. Rankings now depend on input rather than example IDs; edits trigger new searches and invalidate old judgments.
- Six automated tests cover time-sensitive and schedule queries, unrelated/empty/date-only inputs, ranking provenance, negation limitations, edit invalidation, manual browsing, undo and exported search traces.
- Inspection of the six development examples found reference overlap for all five with designated evidence and irrelevant candidates for the sixth. These are development cases, not a held-out evaluation. No general accuracy or learning benefit is claimed.

A separate first-use check used ten newly worded cases saved before execution, with code and corpus unchanged afterwards. Codex authored the cases and expected passage IDs after inspecting the implementation; this is an internal check, not a blind or independently annotated evaluation. Six of seven cases with designated evidence returned the expected passage, all at rank one. One paraphrase returned no candidate. One of three unsupported or outside-topic cases returned irrelevant participant descriptions. Relevant counterevidence also counted as a retrieval hit. These counts do not measure factual judgment, user behaviour or learning gains. Cases, hashes and full traces are in `evaluation/cases.json` and `evaluation/results.json`.

Run the checks from this directory:

```sh
python -m unittest discover -s tests -v
python evaluation/run_check.py
```

## AI assistance and authorship

The student selected the topic and continued without paid API access. Codex assisted with implementing and testing the code, including excerpt checks, editing and recovery checks, and checking that authored summaries and preset judgments do not affect ranking. Earlier report and diagram drafts were prepared with Codex; the student is responsible for the final writing and redrawn figures. Codex also assisted with reference and formatting review. AI-assisted development does not mean a generative model runs in the app. You should review this account and add any further changes or checks you personally perform.

## Additional files and submission status

- [Project report](docs/EvidenceCheck_A2_Report.docx): English report with repository, README and release links. The author should review its claims and contribution statement before submission.
- [System diagram](docs/system-architecture.png), [editable SVG](docs/system-architecture.svg), and storyboards [1](docs/storyboard-1-supported.png), [2](docs/storyboard-2-unit-error.png), [3](docs/storyboard-3-retrieval-recovery.png): inspectable figures; screen sketches are illustrative, not captured screenshots or participant observations.

The submitted prototype is identified by release `a2-submission`. The repository contains the implemented system and its supporting documents; author review is required before coursework submission. This repository packages the final project. The development summary above records the main decisions and checks. Live model integration is optional future work.

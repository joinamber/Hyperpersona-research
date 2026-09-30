# Contributing to HyperPersona

HyperPersona combines software engineering with behavioral-research methodology. Changes should preserve both technical traceability and the distinction between synthetic and human evidence.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -v
```

Run the local API with:

```bash
uvicorn app:app --reload
```

## Pull requests

Keep changes small enough to review. Include:

- the problem being solved;
- implementation summary;
- tests added or updated;
- research-method implications, if any;
- known limitations.

For changes to persona generation, interviewing, extraction, adversarial reasoning, or scoring, state what observable improvement you expect and how it can be evaluated.

## Research safeguards

Do not introduce features that present synthetic frequency as population prevalence or synthetic personas as validated representatives of demographic groups. Preserve evidence provenance and counterexamples.

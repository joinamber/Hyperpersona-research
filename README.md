# HyperPersona

**Synthetic JTBD interviews and adversarial hypothesis testing for early product discovery.**

HyperPersona is an open-source research and engineering project exploring how synthetic behavioral personas can help product teams expand and stress-test hypotheses before recruiting human participants.

The project is aimed at early **problem-solution discovery / Jobs-to-be-Done (JTBD)** research across B2C digital products, B2B/SaaS, and physical products.

> Synthetic evidence is not customer evidence. HyperPersona generates possibilities and challenges hypotheses; human research is required for external validity.

## MVP

The current v0.1.0 engineering slice implements:

```text
Research brief
    |
    v
Brief normalizer
    |
    v
Behavioral cohort (12 personas by default)
    |
    v
Independent JTBD interviews
    |
    v
Atomic observations
    |
    v
Candidate hypothesis
    |
    v
Six-agent adversarial panel
    |
    v
Evidence graph
```

The six adversarial roles are:

- **NULL** — asks whether the problem is trivial or absent.
- **INCUMBENT** — asks whether existing solutions already solve the job.
- **BEHAVIORAL** — searches for behavior inconsistent with the proposed mechanism.
- **CONTEXT** — identifies circumstances where the problem disappears.
- **ALTERNATIVE_CAUSE** — proposes competing causal explanations.
- **BOUNDARY** — narrows where the hypothesis should and should not generalize.

## Important limitation

The MVP currently uses deterministic local logic and a `MockLLM` abstraction. It is intended to validate orchestration, schemas, provenance, persona isolation, interview flow, adversarial routing, and evidence-graph construction before a production LLM is connected.

Do not interpret current generated interviews as empirical consumer research.

## Quick start

Requirements: Python 3.11+ recommended.

```bash
git clone https://github.com/joinamber/Hyperpersona-research.git
cd Hyperpersona-research

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -v
```

Start the API:

```bash
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

FastAPI provides an interactive Swagger interface for exercising the MVP endpoints.

## API workflow

A typical study runs through these endpoints:

```text
POST /v1/studies
POST /v1/studies/{sid}/brief/validate
POST /v1/studies/{sid}/cohort?n=12
POST /v1/studies/{sid}/interviews/run
POST /v1/studies/{sid}/extract
POST /v1/studies/{sid}/adversarial/run
GET  /v1/studies/{sid}/evidence-graph
```

Example study payload:

```json
{
  "domain": "B2B_SAAS",
  "target_actor": "SMB employees",
  "target_situation": "submitting work expenses",
  "problem_hypothesis": "Employees need help because receipts get lost",
  "discovery_goal": "discover unmet jobs and friction",
  "market_context": "UK SMEs"
}
```

## Research principles

HyperPersona is designed around several constraints:

1. **Behavior before demographics.** Personas vary primarily on situations, behaviors, constraints, incumbent solutions, experience, and workarounds.
2. **Independent exploration.** Persona interviews are kept separate to reduce synthetic conformity.
3. **Open discovery before convergence.** The system is intended to surface unknown hypotheses before structured comparison.
4. **Counterexamples are first-class evidence.** Some personas should experience little or no meaningful problem.
5. **Provenance is mandatory.** Observations retain references to persona and interview turns.
6. **Synthetic counts are not prevalence estimates.** A frequency within a generated cohort must never be presented as a percentage of real customers.
7. **Adversarial review is not validation.** Internal robustness remains distinct from evidence observed in humans.

## Repository structure

```text
Hyperpersona-research/
├── app.py
├── requirements.txt
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── docs/
│   └── ARCHITECTURE.md
└── tests/
    └── test_pipeline.py
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the current architecture.

## Current limitations

- In-memory storage only; restarting the process clears studies.
- Deterministic simulated persona answers rather than production model calls.
- Fixed interview questions rather than dynamic JTBD laddering.
- One candidate hypothesis generated per extraction run.
- No embedding-based persona deduplication or insight clustering yet.
- No human-validation ingestion/calibration layer yet.
- No cross-model stability testing yet.

## Roadmap

Near-term research and engineering priorities:

- production LLM gateway with structured outputs;
- persona diversity and semantic deduplication;
- dynamic JTBD interviewer with bounded laddering;
- atomic evidence extraction and clustering;
- persistent study/evidence storage;
- prompt/model versioning and observability;
- bias and demographic-dependence audits;
- human-validation workflow;
- controlled comparison against generic LLM-assisted discovery.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

Changes to persona generation, interviewing, evidence extraction, adversarial reasoning, or scoring should state both the expected technical effect and the research-method implication.

## License

HyperPersona is licensed under the **Apache License 2.0**. Commercial use, modification, and redistribution are permitted subject to the license terms.

See [LICENSE](LICENSE).

## Project status

HyperPersona is an experimental research prototype. Its purpose is to investigate whether synthetic-persona workflows can improve the breadth, falsifiability, and efficiency of early product-discovery hypotheses—not to replace human user research.

# HyperPersona architecture

## Purpose

HyperPersona is a hypothesis-generation and falsification system for early product discovery. The MVP uses synthetic behavioral personas to exercise a JTBD research workflow and an adversarial review workflow.

## Components

### FastAPI application
`app.py` exposes the pipeline as inspectable HTTP endpoints. Uvicorn runs the ASGI application locally.

### Brief normalizer
Reframes a product team's initial problem hypothesis into a neutral discovery question and flags obvious presuppositions.

### Behavioral cohort
Creates an experimental coverage cohort rather than a representative sample. Archetypes include struggler, satisfied incumbent, DIY workaround, expert, switcher, abandoner, non-consumer, resource-constrained, and edge-context roles.

### JTBD interview runtime
Each persona is interviewed independently. The current MVP uses eight fixed questions covering episode, trigger, desired outcome, behavior, friction, workaround, adequacy of the current approach, and a counterexample.

### Evidence extraction
Interview answers become atomic observations. Each observation retains the source persona and interview-turn identifiers. Synthetic episodes are explicitly marked as synthetic provenance.

### Adversarial panel
Six independent critic roles attack the candidate hypothesis:

- NULL: the problem may be trivial or absent.
- INCUMBENT: existing solutions may already solve it.
- BEHAVIORAL: actual behavior may contradict the proposed mechanism.
- CONTEXT: the problem may disappear in some circumstances.
- ALTERNATIVE_CAUSE: the behavior may be real but caused by something else.
- BOUNDARY: the hypothesis may apply only under narrower conditions.

### Evidence graph
The graph exposes support and challenge relationships instead of collapsing disagreement into one answer.

## Epistemic boundary

Synthetic evidence is not external validation. The system must preserve the distinction between:

- simulated possibility;
- internal synthetic robustness;
- externally observed human evidence.

No API or UI should transform synthetic counts into population prevalence.

## Current data lifecycle

All study data is held in the process-local `DB` dictionary. Restarting the server clears it. This is acceptable for the engineering MVP but not for experimental or production use.

## Planned production boundary

A production implementation should separate orchestration, model gateway, persistence, analysis, and audit services; version prompts and models; persist immutable evidence provenance; and validate top hypotheses with human research.

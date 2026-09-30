from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from uuid import uuid4
import hashlib, random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="HyperPersona", description="Synthetic JTBD Interview Panel + Adversarial Panel for early product discovery", version="0.1.0")
DB: dict[str, dict[str, Any]] = {}

class Status(str, Enum):
    DRAFT="DRAFT"; BRIEF_VALIDATED="BRIEF_VALIDATED"; COHORT_GENERATED="COHORT_GENERATED"
    INTERVIEWS_COMPLETE="INTERVIEWS_COMPLETE"; EVIDENCE_EXTRACTED="EVIDENCE_EXTRACTED"
    ADVERSARIAL_REVIEW_COMPLETE="ADVERSARIAL_REVIEW_COMPLETE"

class StudyCreate(BaseModel):
    domain: Literal["B2C_DIGITAL","B2B_SAAS","PHYSICAL_PRODUCT"]
    target_actor: str
    target_situation: str
    problem_hypothesis: str = ""
    discovery_goal: str
    market_context: str = ""
    known_alternatives: list[str] = []
    known_constraints: list[str] = []

class Brief(BaseModel):
    original_hypothesis: str
    framing_flags: list[dict[str,str]]
    neutral_primary_question: str
    secondary_questions: list[str]

class Persona(BaseModel):
    persona_id: str
    archetype: str
    context: dict[str,str]
    behavior: dict[str,str]
    constraints: dict[str,str]
    motivation: dict[str,str]
    history: dict[str,str]

class Turn(BaseModel):
    turn_id: str
    speaker: Literal["INTERVIEWER","PERSONA"]
    text: str
    provenance: Literal["PROMPT","PROFILE_GIVEN","PROFILE_DERIVED","SIMULATED_EPISODE","MODEL_GENERALIZATION"]

class Observation(BaseModel):
    observation_id: str
    persona_id: str
    source_turn_ids: list[str]
    situation: str = ""
    trigger: str = ""
    job: str = ""
    behavior: str = ""
    friction: str = ""
    workaround: str = ""
    desired_outcome: str = ""
    barrier: str = ""
    polarity: Literal["SUPPORT","COUNTEREXAMPLE","NEUTRAL"]
    provenance: str

class Challenge(BaseModel):
    challenge_id: str
    hypothesis_id: str
    critic: Literal["NULL","INCUMBENT","BEHAVIORAL","CONTEXT","ALTERNATIVE_CAUSE","BOUNDARY"]
    finding: str

class LLM:
    async def generate(self, task: str, payload: dict[str,Any]) -> dict[str,Any]:
        raise NotImplementedError

class MockLLM(LLM):
    """Deterministic local stand-in. It preserves orchestration contracts but is not a behavioral model."""
    async def generate(self, task: str, payload: dict[str,Any]) -> dict[str,Any]:
        if task == "normalize_brief":
            h=payload.get("problem_hypothesis","")
            flags=[]
            if any(w in h.lower() for w in ["need","want","because","prefer","pain"]):
                flags.append({"type":"PRESUPPOSITION","text":h,"reason":"Hypothesis may presuppose a problem or mechanism."})
            return {"original_hypothesis":h,"framing_flags":flags,
                    "neutral_primary_question":f"How does {payload['target_actor']} currently handle {payload['target_situation']}?",
                    "secondary_questions":["What triggers the job?","What is done today?","When is the current approach adequate?","Where does friction occur?","What happens when nothing is done?"]}
        raise NotImplementedError(task)

llm: LLM = MockLLM()
ARCHETYPES=["FREQUENT_STRUGGLER","OCCASIONAL_STRUGGLER","SATISFIED_INCUMBENT","DIY_WORKAROUND","EXPERT_POWER_USER","RECENT_SWITCHER","ABANDONER","NON_CONSUMER","RESOURCE_CONSTRAINED","EDGE_CONTEXT","SATISFIED_INCUMBENT","DIY_WORKAROUND"]
SOLUTIONS=["manual process","incumbent software","spreadsheet/checklist","delegation","no dedicated solution","hybrid tools"]
FREQ=["daily","weekly","monthly","rare"]

@app.post('/v1/studies')
async def create_study(req: StudyCreate):
    sid='STU_'+uuid4().hex[:10]
    DB[sid]={"study":req.model_dump()|{"study_id":sid,"status":Status.DRAFT},"events":[]}
    event(sid,"STUDY_CREATED")
    return {"study_id":sid,"status":Status.DRAFT,"next_action":"VALIDATE_BRIEF"}

@app.get('/v1/studies/{sid}')
async def get_study(sid:str):
    return require(sid)

@app.post('/v1/studies/{sid}/brief/validate')
async def validate_brief(sid:str):
    d=require(sid); brief=Brief(**await llm.generate("normalize_brief",d["study"]))
    d["brief"]=brief.model_dump(); d["study"]["status"]=Status.BRIEF_VALIDATED; event(sid,"BRIEF_VALIDATED")
    return brief

@app.post('/v1/studies/{sid}/cohort')
async def cohort(sid:str, n:int=12):
    d=require(sid)
    if "brief" not in d: raise HTTPException(409,"Validate brief first")
    n=max(4,min(n,36)); personas=[]
    for i in range(n):
        arch=ARCHETYPES[i%len(ARCHETYPES)]
        rng=random.Random(stable_seed(sid+str(i)))
        adequate=arch in {"SATISFIED_INCUMBENT","NON_CONSUMER","EXPERT_POWER_USER"}
        p=Persona(
            persona_id=f"PER_{i+1:03d}", archetype=arch,
            context={"role_in_situation":d['study']['target_actor'],"environment":rng.choice(["routine","time-pressured","mobile/remote","collaborative"]),"job_frequency":rng.choice(FREQ)},
            behavior={"current_solution":rng.choice(SOLUTIONS),"experience_level":rng.choice(["low","moderate","high"]),"habit_strength":rng.choice(["low","moderate","high"]),"switching_history":rng.choice(["none","tried alternative","recently switched"])},
            constraints={"time":rng.choice(["low","moderate","high"]),"money":rng.choice(["low","moderate","high"]),"access":rng.choice(["limited","normal"]),"authority":rng.choice(["self-directed","requires approval"])},
            motivation={"primary_goal":f"complete {d['study']['target_situation']} with acceptable effort","competing_goal":rng.choice(["save time","avoid errors","maintain control","avoid disruption"]),"risk_orientation":rng.choice(["low","moderate","high"])},
            history={"recent_event":"routine episode","previous_failure":"none material" if adequate else "a prior attempt created avoidable rework","learned_workaround":"continue current approach" if adequate else rng.choice(["batch work","double-check","keep a manual backup","ask another person"])} )
        personas.append(p.model_dump())
    d["personas"]=personas; d["study"]["status"]=Status.COHORT_GENERATED; event(sid,"COHORT_GENERATED",{"n":n})
    return {"personas":personas,"warning":"Experimental coverage cohort; counts are not population estimates."}

QUESTIONS=[
 "Think about the most recent time you dealt with this situation. What was happening?",
 "What triggered you to act?",
 "What were you trying to accomplish?",
 "Walk me through what you actually did.",
 "What, if anything, became difficult?",
 "What did you do about that?",
 "What was good enough about the approach you already had?",
 "Tell me about a time when this was easy or not a meaningful problem.",
]

def persona_answer(p:dict[str,Any], qidx:int, situation:str)->str:
    adequate=p['archetype'] in {"SATISFIED_INCUMBENT","NON_CONSUMER","EXPERT_POWER_USER"}
    vals=[
      f"The last time involved {situation} in a {p['context']['environment']} setting; I used {p['behavior']['current_solution']}.",
      f"The trigger was needing to complete the task while also trying to {p['motivation']['competing_goal']}.",
      f"I wanted to {p['motivation']['primary_goal']}.",
      f"I followed my usual {p['behavior']['current_solution']} process and relied on a {p['history']['learned_workaround']} pattern where needed.",
      "Nothing significant became difficult; the existing approach was adequate." if adequate else f"The main friction was interruption and rework when constraints were {p['constraints']['time']} on time.",
      "I kept the existing process because changing it would add effort." if adequate else f"I used the workaround: {p['history']['learned_workaround']}.",
      f"The current approach is familiar and its habit strength is {p['behavior']['habit_strength']}.",
      "When the task is routine and there is enough time, I do not experience a meaningful problem."
    ]
    return vals[qidx]

@app.post('/v1/studies/{sid}/interviews/run')
async def interviews(sid:str):
    d=require(sid)
    if not d.get("personas"): raise HTTPException(409,"Generate cohort first")
    sessions=[]
    for p in d['personas']:
        turns=[]
        for i,q in enumerate(QUESTIONS):
            turns.append(Turn(turn_id='T_'+uuid4().hex[:8],speaker="INTERVIEWER",text=q,provenance="PROMPT").model_dump())
            turns.append(Turn(turn_id='T_'+uuid4().hex[:8],speaker="PERSONA",text=persona_answer(p,i,d['study']['target_situation']),provenance="SIMULATED_EPISODE").model_dump())
        sessions.append({"session_id":"INT_"+uuid4().hex[:8],"persona_id":p['persona_id'],"turns":turns})
    d['interviews']=sessions; d['study']['status']=Status.INTERVIEWS_COMPLETE; event(sid,"INTERVIEWS_COMPLETE")
    return {"sessions":sessions,"warning":"All episodes are synthetic unless explicitly grounded otherwise."}

@app.post('/v1/studies/{sid}/extract')
async def extract(sid:str):
    d=require(sid)
    if not d.get('interviews'): raise HTTPException(409,"Run interviews first")
    pmap={p['persona_id']:p for p in d['personas']}; obs=[]
    for s in d['interviews']:
        p=pmap[s['persona_id']]; answers=[t for t in s['turns'] if t['speaker']=='PERSONA']
        adequate=p['archetype'] in {"SATISFIED_INCUMBENT","NON_CONSUMER","EXPERT_POWER_USER"}
        o=Observation(observation_id='OBS_'+uuid4().hex[:8],persona_id=p['persona_id'],source_turn_ids=[x['turn_id'] for x in answers],
          situation=answers[0]['text'],trigger=answers[1]['text'],job=answers[2]['text'],behavior=answers[3]['text'],friction=answers[4]['text'],workaround=answers[5]['text'],desired_outcome=p['motivation']['primary_goal'],barrier="existing approach is adequate" if adequate else "time/interruption cost",polarity="COUNTEREXAMPLE" if adequate else "SUPPORT",provenance="SIMULATED_EPISODE")
        obs.append(o.model_dump())
    d['observations']=obs
    supports=[o for o in obs if o['polarity']=='SUPPORT']; counters=[o for o in obs if o['polarity']=='COUNTEREXAMPLE']
    hypothesis={"hypothesis_id":"H001","statement":f"When {d['study']['target_actor']} handles {d['study']['target_situation']} under competing constraints, interruption and rework may create friction even when existing approaches remain adequate in some contexts.","supporting_observation_ids":[o['observation_id'] for o in supports],"counterexample_ids":[o['observation_id'] for o in counters],"synthetic_status":"UNVALIDATED"}
    d['hypotheses']=[hypothesis]; d['study']['status']=Status.EVIDENCE_EXTRACTED; event(sid,"EVIDENCE_EXTRACTED")
    return {"observations":obs,"hypotheses":[hypothesis]}

CRITICS={
 "NULL":"The problem may be trivial when the current process is routine and familiar.",
 "INCUMBENT":"Existing software, manual routines, or delegation may already solve the job adequately.",
 "BEHAVIORAL":"Some people may complete the task immediately rather than batch or defer it, avoiding the proposed friction.",
 "CONTEXT":"The problem may disappear when time pressure is low or the workflow is routine.",
 "ALTERNATIVE_CAUSE":"Observed rework could be caused by policy ambiguity, coordination, or approval rather than the hypothesized mechanism.",
 "BOUNDARY":"The hypothesis should be limited to contexts with competing demands or process interruptions and not generalized to all users."
}

@app.post('/v1/studies/{sid}/adversarial/run')
async def adversarial(sid:str):
    d=require(sid)
    if not d.get('hypotheses'): raise HTTPException(409,"Extract hypotheses first")
    out=[]
    for h in d['hypotheses']:
        for critic,finding in CRITICS.items():
            out.append(Challenge(challenge_id='CH_'+uuid4().hex[:8],hypothesis_id=h['hypothesis_id'],critic=critic,finding=finding).model_dump())
    d['challenges']=out; d['study']['status']=Status.ADVERSARIAL_REVIEW_COMPLETE; event(sid,"ADVERSARIAL_REVIEW_COMPLETE")
    return {"challenges":out}

@app.get('/v1/studies/{sid}/evidence-graph')
async def graph(sid:str):
    d=require(sid); nodes=[]; edges=[]
    for o in d.get('observations',[]):
        nodes.append({"id":o['observation_id'],"type":"OBSERVATION","label":o['friction']})
    for h in d.get('hypotheses',[]):
        nodes.append({"id":h['hypothesis_id'],"type":"HYPOTHESIS","label":h['statement'],"status":h['synthetic_status']})
        for oid in h['supporting_observation_ids']: edges.append({"source":oid,"target":h['hypothesis_id'],"relationship":"SUPPORTS"})
        for oid in h['counterexample_ids']: edges.append({"source":oid,"target":h['hypothesis_id'],"relationship":"CHALLENGES"})
    for c in d.get('challenges',[]):
        nodes.append({"id":c['challenge_id'],"type":"ADVERSARIAL_FINDING","label":c['finding'],"critic":c['critic']})
        edges.append({"source":c['challenge_id'],"target":c['hypothesis_id'],"relationship":"CHALLENGES"})
    return {"nodes":nodes,"edges":edges,"epistemic_notice":"Simulation generates possibilities; human research is required for external validity."}

def stable_seed(x:str)->int: return int(hashlib.sha256(x.encode()).hexdigest()[:8],16)
def require(sid:str):
    if sid not in DB: raise HTTPException(404,"Study not found")
    return DB[sid]
def event(sid:str,typ:str,payload:dict|None=None): DB[sid]['events'].append({"type":typ,"payload":payload or {}})

from fastapi.testclient import TestClient
from app import app

c=TestClient(app)

def test_end_to_end():
    r=c.post('/v1/studies',json={"domain":"B2B_SAAS","target_actor":"SMB employees","target_situation":"submitting work expenses","problem_hypothesis":"Employees need help because receipts get lost","discovery_goal":"discover unmet jobs and friction","market_context":"UK SMEs"})
    assert r.status_code==200
    sid=r.json()['study_id']
    assert c.post(f'/v1/studies/{sid}/brief/validate').status_code==200
    cohort=c.post(f'/v1/studies/{sid}/cohort?n=12').json()['personas']
    assert len(cohort)==12
    ints=c.post(f'/v1/studies/{sid}/interviews/run').json()['sessions']
    assert len(ints)==12 and all(len(x['turns'])==16 for x in ints)
    ex=c.post(f'/v1/studies/{sid}/extract').json()
    assert len(ex['observations'])==12 and ex['hypotheses'][0]['synthetic_status']=='UNVALIDATED'
    adv=c.post(f'/v1/studies/{sid}/adversarial/run').json()['challenges']
    assert len(adv)==6
    g=c.get(f'/v1/studies/{sid}/evidence-graph').json()
    assert any(n['type']=='HYPOTHESIS' for n in g['nodes'])
    assert any(e['relationship']=='CHALLENGES' for e in g['edges'])

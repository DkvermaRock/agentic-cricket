from concurrent.futures import ThreadPoolExecutor
import os
import uuid
import threading

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from backend.app import create_app
from backend.game import ATTRIBUTES, cost, evaluate, play_over, train

SKILLS={"power":65,"timing":60,"composure":55}

@pytest.fixture(params=['sqlite']+(['postgres'] if os.environ.get('CRICKET_TEST_POSTGRES_URL') else []))
def app(tmp_path,request):
    if request.param=='sqlite':
        app=create_app(tmp_path/'arena.sqlite3')
        yield app
        app.state.store.engine.dispose()
        return
    url=make_url(os.environ['CRICKET_TEST_POSTGRES_URL']).set(drivername='postgresql+psycopg')
    assert url.host in {'127.0.0.1','localhost','::1'}, 'Tests require a disposable local PostgreSQL server'
    name='boundary_test_'+uuid.uuid4().hex
    admin=create_engine(url,isolation_level='AUTOCOMMIT')
    with admin.connect() as db: db.exec_driver_sql(f'CREATE DATABASE "{name}"')
    app=None
    try:
        app=create_app(url.set(database=name).render_as_string(hide_password=False))
        yield app
    finally:
        if app: app.state.store.engine.dispose()
        with admin.connect() as db: db.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()

@pytest.fixture
def client(app):
    with TestClient(app) as client: yield client

def make(client,name='Nila Storm',**skills):
    return client.post('/api/players',json={"name":name,**(skills or SKILLS)})

def test_budget_and_rollback(client):
    assert make(client).status_code==201
    assert make(client,'Kai Pace').status_code==201
    assert make(client,'Mira Spin').status_code==409
    assert client.get('/api/meta').json()['coins']==100-2*cost(SKILLS)
    assert len(client.get('/api/players').json())==2

def test_unicode_name_race(app):
    def attempt(name):
        with TestClient(app) as client:return make(client,name,power=10,timing=10,composure=10).status_code
    with ThreadPoolExecutor(3) as pool:
        assert sorted(pool.map(attempt,['Nila Storm',' NILA   STORM ','Ｎｉｌａ Ｓｔｏｒｍ']))==[201,409,409]
    with TestClient(app) as client: assert client.get('/api/meta').json()['coins']==90

def test_budget_race(app):
    def attempt(i):
        with TestClient(app) as client:return make(client,f'Elite {i}',power=95,timing=95,composure=95).status_code
    with ThreadPoolExecutor(3) as pool: assert sorted(pool.map(attempt,range(3)))==[201,409,409]
    with TestClient(app) as client: assert client.get('/api/meta').json()['coins']==0

@pytest.mark.parametrize('name',['ab','1234','Invisible\u200bName','Bad<script>','A'*25])
def test_invalid_names(client,name): assert make(client,name).status_code==422

@pytest.mark.parametrize('power',[9,96,True,65.2,'65'])
def test_invalid_skills(client,power): assert make(client,power=power,timing=60,composure=55).status_code==422

def test_deterministic_stored_trajectories():
    for seed in range(80):
        r=play_over(SKILLS,{},seed)
        assert r==play_over(SKILLS,{},seed)
        assert r['score']==sum(e['runs'] for e in r['events'])
        assert 1<=len(r['events'])<=6
        assert all(not e['out'] for e in r['events'][:-1])
        assert len(r['events'])==6 or r['wickets'] or r['won']
        for e in r['events']:
            assert e['trajectory']['bounce'][1]==.045
            assert e['trajectory']['bounce'][2]<e['trajectory']['contact'][2]
            assert e['duration']>=8.5

def test_ability_levels_affect_distribution():
    weak={k:10 for k in ATTRIBUTES};strong={k:95 for k in ATTRIBUTES}
    assert sum(play_over(strong,{},s,24)['score'] for s in range(500)) > sum(play_over(weak,{},s,24)['score'] for s in range(500))*1.3

@pytest.mark.parametrize('seed',[11,29,47])
def test_learning_on_unseen_samples(seed):
    candidate=train(SKILLS,{},seed)
    result=evaluate(SKILLS,{},candidate,seed+1000)
    assert result['accepted'] and result['utility_delta']['low']>0
    assert SKILLS=={"power":65,"timing":60,"composure":55}
    identical=evaluate(SKILLS,candidate,candidate,seed+2000)
    assert not identical['accepted'] and identical['utility_delta']['mean']==0

def test_learning_persistence_and_snapshot(client,app):
    p=make(client).json()
    match=client.post(f"/api/players/{p['id']}/matches",json={'seed':100}).json()
    for _ in range(3):
        response=client.post(f"/api/players/{p['id']}/train").json()
        assert response['report']['training_seed']!=response['report']['evaluation_seed']
    assert client.post(f"/api/players/{p['id']}/train").status_code==409
    with TestClient(create_app(app.state.store.path)) as reopened:
        saved=reopened.get('/api/players').json()[0]
        assert saved['id']==p['id'] and saved['training_balls']==6000
        assert all(saved[k]==p[k] for k in ATTRIBUTES)
        assert reopened.get(f"/api/players/{p['id']}/matches").json()[0]==match
        assert len(reopened.get(f"/api/players/{p['id']}/reports").json())==3

def test_concurrent_training(app,monkeypatch):
    import importlib
    module=importlib.import_module('backend.app');real=module.train;barrier=threading.Barrier(2)
    def synchronized(*args,**kwargs):barrier.wait(timeout=10);return real(*args,**kwargs)
    monkeypatch.setattr(module,'train',synchronized)
    with TestClient(app) as client:p=make(client).json()
    def attempt(_):
        with TestClient(app) as client:return client.post(f"/api/players/{p['id']}/train").status_code
    with ThreadPoolExecutor(2) as pool: assert sorted(pool.map(attempt,range(2)))==[200,409]
    with TestClient(app) as client: assert client.get('/api/players').json()[0]['training_balls']==2000

def test_failed_candidate_not_deployed(client,monkeypatch):
    import importlib
    module=importlib.import_module('backend.app');real=module.evaluate
    def rejected(*args,**kwargs):return {**real(*args,**kwargs),'accepted':False}
    monkeypatch.setattr(module,'evaluate',rejected)
    p=make(client).json();r=client.post(f"/api/players/{p['id']}/train").json()
    assert r['player']['version']==0 and r['player']['training_balls']==2000
    assert not r['player']['lessons']

def test_exhibition_does_not_spend_or_create_players(client):
    result=client.get('/api/exhibition').json()
    assert len(result['match']['events'])==6
    assert result['match']['exhibition']
    assert client.get('/api/players').json()==[]
    assert client.get('/api/meta').json()['coins']==100

def test_hosted_authentication(tmp_path,monkeypatch):
    monkeypatch.setenv('CRICKET_REQUIRE_AUTH','true')
    monkeypatch.delenv('CRICKET_DEMO_PASSWORD',raising=False)
    with pytest.raises(ValueError,match='PASSWORD'):create_app(tmp_path/'private.sqlite3')
    monkeypatch.setenv('CRICKET_DEMO_PASSWORD','test-only-long-password')
    with TestClient(create_app(tmp_path/'private.sqlite3')) as c:
        assert c.get('/api/health').status_code==200
        for url in ['/','/api/players','/api/exhibition','/docs']:
            assert c.get(url).status_code==401
        assert c.get('/api/meta',auth=('cricket','test-only-long-password')).status_code==200
        assert c.get('/api/meta',headers={'Authorization':'Basic invalid'}).status_code==401

def test_postgres_browser_role_has_no_row_access(app):
    if not app.state.store.postgres:
        pytest.skip('RLS is a PostgreSQL integration check')
    role='boundary_role_'+uuid.uuid4().hex
    engine=app.state.store.engine
    with engine.begin() as db:
        db.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN')
    try:
        with engine.begin() as db:
            db.exec_driver_sql(f'GRANT USAGE ON SCHEMA public TO "{role}"')
            db.exec_driver_sql(f'GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO "{role}"')
            db.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            for table in ('club','players','reports','matches'):
                assert db.exec_driver_sql(f'SELECT count(*) FROM {table}').scalar_one()==0
        with pytest.raises(Exception,match='row-level security'):
            with engine.begin() as db:
                db.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
                db.exec_driver_sql('INSERT INTO club VALUES (1,500)')
    finally:
        with engine.begin() as db:
            db.exec_driver_sql(f'DROP OWNED BY "{role}"')
            db.exec_driver_sql(f'DROP ROLE "{role}"')

"""Provisioning safeguards; these tests never call the external API."""
import pytest

from deploy import create_supabase as cloud


@pytest.fixture
def api(monkeypatch):
    for key in ('SUPABASE_ORGANIZATION_ID', 'SUPABASE_PROJECT_NAME', 'SUPABASE_REGION', 'SUPABASE_DB_PASSWORD'):
        monkeypatch.delenv(key, raising=False)
    calls = []
    responses = {
        '/organizations': [{'id': 'org-one', 'slug': 'org-one'}],
        '/organizations/org-one': {'plan': 'free'},
        '/projects': [],
        '/projects/available-regions?organization_slug=org-one': {'all': {'specific': [{'code': 'us-east-1'}]}},
    }

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == 'POST':
            return {'ref': 'project-ref', 'name': payload['name'], 'region': 'us-east-1', 'status': 'COMING_UP', 'db_pass': 'must-not-be-returned'}
        return responses[path]

    monkeypatch.setattr(cloud, 'api', request)
    return calls, responses


def test_plan_is_read_only_and_create_filters_output(api, monkeypatch):
    calls, _ = api
    plan = cloud.prepare()
    assert plan['name'] == 'agentic-cricket-poc' and plan['plan'] == 'free'
    assert all(method == 'GET' for method, _, _ in calls)
    monkeypatch.setenv('SUPABASE_DB_PASSWORD', 'test-only-password')
    result = cloud.create(plan)
    assert result == {'ref': 'project-ref', 'name': plan['name'], 'region': 'us-east-1', 'status': 'COMING_UP'}
    assert calls[-1] == ('POST', '/projects', {'name': plan['name'], 'organization_slug': 'org-one', 'region_selection': {'type': 'specific', 'code': 'us-east-1'}, 'db_pass': 'test-only-password'})


def test_existing_project_is_reused_without_password(api):
    calls, responses = api
    responses['/projects'] = [{'ref': 'existing-ref', 'name': 'agentic-cricket-poc', 'organization_slug': 'org-one'}]
    assert cloud.create(cloud.prepare())['ref'] == 'existing-ref'
    assert all(method == 'GET' for method, _, _ in calls)


@pytest.mark.parametrize('plan', ['pro', None])
def test_paid_or_unknown_plan_does_not_create(api, plan):
    calls, responses = api
    responses['/organizations/org-one']['plan'] = plan
    with pytest.raises(RuntimeError, match='Free organization'):
        cloud.prepare()
    assert all(method == 'GET' for method, _, _ in calls)


@pytest.mark.parametrize('organizations', [[], [{'id': 'one'}, {'id': 'two'}]])
def test_organization_choice_is_required_when_ambiguous(api, organizations):
    _, responses = api
    responses['/organizations'] = organizations
    with pytest.raises(RuntimeError, match='SUPABASE_ORGANIZATION_ID'):
        cloud.prepare()


def test_unavailable_region_and_missing_password_block_creation(api):
    calls, responses = api
    plan = cloud.prepare()
    with pytest.raises(RuntimeError, match='SUPABASE_DB_PASSWORD'):
        cloud.create(plan)
    responses['/projects/available-regions?organization_slug=org-one']['all']['specific'][0]['status'] = 'capacity'
    with pytest.raises(RuntimeError, match='unavailable'):
        cloud.prepare()
    assert all(method == 'GET' for method, _, _ in calls)

"""Create the requested fresh project using secure Management API credentials."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def api(method,path,payload=None):
    token=os.environ.get('SUPABASE_ACCESS_TOKEN')
    if not token: raise RuntimeError('Add SUPABASE_ACCESS_TOKEN in secure environment settings.')
    req=Request('https://api.supabase.com/v1'+path,method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urlopen(req,timeout=30) as r: return json.load(r)
    except HTTPError as e:
        raise RuntimeError(f'Supabase HTTP {e.code}. Check account access, network settings and project quota.') from None
    except (URLError,TimeoutError,ValueError):
        raise RuntimeError('Request did not complete. Check the Supabase dashboard before retrying creation; it may already exist.') from None


def prepare():
    org=os.environ.get('SUPABASE_ORGANIZATION_ID','')
    if not org:
        organizations=api('GET','/organizations')
        if len(organizations)==1: org=organizations[0].get('slug',organizations[0]['id'])
        else: raise RuntimeError('Set SUPABASE_ORGANIZATION_ID to the intended organization slug. Use --organizations to list them.')
    if not re.fullmatch(r'[\w-]+',org,flags=re.ASCII): raise RuntimeError('Invalid organization slug.')
    organization=api('GET','/organizations/'+org)
    if organization.get('plan')!='free': raise RuntimeError('This temporary setup requires a verified Free organization; no paid plan will be selected automatically.')
    name=os.environ.get('SUPABASE_PROJECT_NAME','agentic-cricket-poc')
    matches=[p for p in api('GET','/projects') if p.get('name')==name and p.get('organization_slug',p.get('organization_id'))==org]
    if len(matches)>1: raise RuntimeError('Multiple projects have this name. Select the intended project in the dashboard.')
    if matches: return {'action':'existing','project':public(matches[0])}
    region=os.environ.get('SUPABASE_REGION','us-east-1')
    regions=api('GET','/projects/available-regions?'+urlencode({'organization_slug':org}))
    if not any(r['code']==region and not r.get('status') for r in regions['all']['specific']): raise RuntimeError('Selected region is unavailable. Set SUPABASE_REGION to an available region.')
    return {'action':'create','name':name,'organization_slug':org,'region':region,'plan':'free'}


def public(p):return {k:p.get(k) for k in ('ref','name','region','status')}


def create(plan):
    if plan['action']=='existing': return plan['project']
    password=os.environ.get('SUPABASE_DB_PASSWORD')
    if not password: raise RuntimeError('Add SUPABASE_DB_PASSWORD in secure environment settings.')
    return public(api('POST','/projects',{'name':plan['name'],'organization_slug':plan['organization_slug'],'region_selection':{'type':'specific','code':plan['region']},'db_pass':password}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create',action='store_true')
    parser.add_argument('--organizations',action='store_true')
    args=parser.parse_args()
    try:
        if args.organizations:
            print(json.dumps([{k:p.get(k) for k in ('id','slug','name')} for p in api('GET','/organizations')],indent=2))
        else:
            plan=prepare();result=create(plan) if args.create else plan
            if args.create:
                path=Path('build/cloud/supabase-project.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result,indent=2))
    except RuntimeError as error:
        print(str(error),file=sys.stderr);raise SystemExit(1)

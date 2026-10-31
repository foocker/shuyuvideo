"""Behavioral tests for Astra audits, render repair, and safe resumption."""
import json
from pathlib import Path
import pytest
from astra.models import Artifact, Assessment, Request
from astra.pipeline import Pipeline
from astra.rendering import validate_source
from astra.client import clean_environment

SOURCE='from manim import *\nclass AstraFilm(ThreeDScene):\n    def construct(self):\n        self.wait(30)\n'

def verdict(evidence, reject=False, target='scene'):
    return Assessment(mathematics=.5 if reject else .95,pedagogy=.95,visual_design=.95,
                      implementation=.95,verified=True,defects=['fix'] if reject else [],
                      feedback='repair the named defect',evidence=evidence,
                      limitations=['model judgment'],repair_stage=target)

class FakeSDK:
    def __init__(self, rejected_stage=None):
        self.calls=[];self.rejected_stage=rejected_stage
    def call(self,prompt,**kw):
        self.calls.append(kw['output'].name)
        if kw['schema'] is Artifact:
            return Artifact(summary='complete',content=SOURCE if 'scene-candidate' in kw['output'].name else 'checked plan',checks=['done'],sources=[])
        # The manifest names exact supplied artifacts; use candidate or attached frame.
        candidates=sorted(kw['cwd'].glob('attempts/*-candidate.json'))
        evidence=[kw['images'][0].relative_to(kw['cwd']).as_posix()] if kw['images'] else [candidates[-1].relative_to(kw['cwd']).as_posix()]
        reject=self.rejected_stage and self.rejected_stage in kw['output'].name
        self.rejected_stage=None if reject else self.rejected_stage
        return verdict(evidence,reject=bool(reject),target='mathematics')

def fake_probe(folder,source,attempt):
    p=folder/f'probes/{attempt:03d}';p.mkdir(parents=True)
    record=p/'execution.json';record.write_text('{}')
    frame=p/'frame.png';frame.write_bytes(b'test')
    return record,frame

def fake_render(folder,source,quality,attempt):
    p=folder/f'renders/{attempt:03d}';p.mkdir(parents=True)
    paths=[p/n for n in ('film.mp4','frame.png','sheet.png')]
    for path in paths:path.write_bytes(b'test')
    return paths[0],[paths[1]],paths[2]

def test_all_stages_and_render_receive_independent_astra_audits(tmp_path):
    client=FakeSDK()
    result=Pipeline(client,tmp_path,fake_render,prober=fake_probe).run(Request(prompt='Explain topology'))
    assert result['status']=='completed' and result['review_status']=='astra_only'
    assert result['evaluator']=='gpt-6-astra'
    assert len(result['events'])==5 and all(e['approved'] for e in result['events'])
    assert len(client.calls)==9 and result['video_sha256']
    assert all('verified' in e['review'] for e in result['events'])


@pytest.mark.parametrize('stage', ['mathematics', 'scene', 'render'])
def test_audit_defects_are_retained_without_automatic_regeneration(tmp_path,stage):
    client=FakeSDK(stage)
    result=Pipeline(client,tmp_path,fake_render,prober=fake_probe).run(Request(prompt='Explain topology'))
    assert result['status']=='completed' and result['review_status']=='astra_only'
    assert len(client.calls)==9
    rejected=[e for e in result['events'] if not e['approved']]
    assert len(rejected)==1 and rejected[0]['stage']==stage
    assert rejected[0]['review']['defects']==['fix']


@pytest.mark.parametrize('legacy_mode', ['off', 'advisory', 'gated'])
def test_old_saved_requests_resume_without_reenabling_retired_review(tmp_path,legacy_mode):
    client=FakeSDK()
    pipe=Pipeline(client,tmp_path,fake_render,prober=fake_probe)
    first=pipe.run(Request(prompt='Explain topology'))
    folder=Path(first['run_dir'])
    request_path=folder/'request.json'
    data=json.loads(request_path.read_text(encoding='utf-8'))
    data['review_mode']=legacy_mode
    request_path.write_text(json.dumps(data),encoding='utf-8')
    original=request_path.read_bytes()
    # Rebind the saved input hash to emulate a request written by the old entry.
    from astra.pipeline import digest,save
    for stage in first['stages'].values():
        stage['hashes']['request.json']=digest(request_path)
    first['review_mode']=legacy_mode
    save(folder/'manifest.json',first)
    client.calls.clear()
    resumed=pipe.run(None,folder=folder)
    assert len(client.calls)==1 and resumed['review_status']=='astra_only'
    assert 'review_mode' not in resumed
    assert request_path.read_bytes()==original


def test_new_requests_exclude_retired_settings_but_keep_strict_validation(tmp_path):
    assert 'review_mode' not in Request.model_json_schema()['properties']
    for bad in [{'review_mode':'invalid'}, {'unexpected':True}]:
        path=tmp_path/'request.json'
        path.write_text(json.dumps(dict(prompt='Explain topology',**bad)),encoding='utf-8')
        with pytest.raises(ValueError):
            Request.from_file(path)


def test_audit_failure_records_failed_run_without_rendering(tmp_path):
    class OfflineSDK(FakeSDK):
        def call(self,prompt,**kw):
            if kw['schema'] is Assessment:
                raise ConnectionError('audit offline')
            return super().call(prompt,**kw)
    with pytest.raises(ConnectionError,match='offline'):
        Pipeline(OfflineSDK(),tmp_path,lambda *a:pytest.fail('must not render'),prober=fake_probe).run(Request(prompt='Explain topology'))
    assert json.loads(next(tmp_path.glob('*/manifest.json')).read_text())['status']=='failed'


def test_local_render_never_constructs_model_clients(tmp_path,monkeypatch):
    import astra.local_render as local
    folder=tmp_path/'run';folder.mkdir()
    (folder/'manifest.json').write_text('{"events":[]}')
    scene=folder/'saved.py';scene.write_text(SOURCE)
    monkeypatch.setattr(local,'render',fake_render)
    monkeypatch.setattr('astra.pipeline.CodexSDK',lambda:pytest.fail('No model clients permitted'))
    result=local.render_existing(folder,scene)
    assert result['status']=='completed' and result['review_status']=='not_reviewed'
    assert 'review_mode' not in result
    assert result['video_sha256']

def test_exhausted_static_repair_budget_fails_without_render(tmp_path):
    class InvalidSDK(FakeSDK):
        def call(self,prompt,**kw):
            result=super().call(prompt,**kw)
            if kw['schema'] is Artifact and 'scene-candidate' in kw['output'].name:
                result.content='import os\n'+SOURCE
            return result
    with pytest.raises(RuntimeError,match='budget'):
        Pipeline(InvalidSDK(),tmp_path,lambda *a:pytest.fail('must not render'),prober=fake_probe).run(Request(prompt='Explain topology',max_revisions=0))
    assert json.loads(next(tmp_path.glob('*/manifest.json')).read_text())['status']=='failed'


def test_render_error_repairs_only_scene_and_retains_error(tmp_path):
    calls=[]
    def renderer(folder,source,quality,attempt):
        calls.append(attempt)
        if len(calls)==1:
            raise RuntimeError('render failure')
        return fake_render(folder,source,quality,attempt)
    client=FakeSDK()
    result=Pipeline(client,tmp_path,renderer,prober=fake_probe).run(Request(prompt='Explain topology'))
    assert result['status']=='completed' and len(calls)==2
    assert sum('scene-candidate' in c for c in client.calls)==2
    assert sum('mathematics-candidate' in c for c in client.calls)==1
    assert any(e.get('error')=='render failure' for e in result['events'])


def test_resume_rechecks_render_and_changed_artifacts(tmp_path):
    client=FakeSDK();pipe=Pipeline(client,tmp_path,fake_render,prober=fake_probe)
    first=pipe.run(Request(prompt='Explain topology'));folder=Path(first['run_dir'])
    client.calls.clear();pipe.run(None,folder=folder)
    assert len(client.calls)==1 and 'render-astra-audit' in client.calls[0]
    (folder/'mathematics.json').write_text('{}')
    client.calls.clear();pipe.run(None,folder=folder)
    assert sum('candidate' in c for c in client.calls)==3

def test_credentials_not_inherited(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-secret');monkeypatch.setenv('CODEX_API_KEY','test')
    monkeypatch.setenv('XAI_API_KEY','test');monkeypatch.setenv('GH_TOKEN','test')
    env=clean_environment()
    assert not {'OPENAI_API_KEY','CODEX_API_KEY','XAI_API_KEY','GH_TOKEN'} & env.keys()


def test_resume_quality_preserves_planning_but_rechecks_scene(tmp_path):
    client=FakeSDK();qualities=[]
    def renderer(folder,source,quality,attempt):
        qualities.append(quality)
        return fake_render(folder,source,quality,attempt)
    pipe=Pipeline(client,tmp_path,renderer,prober=fake_probe)
    first=pipe.run(Request(prompt='Explain topology'));folder=Path(first['run_dir'])
    client.calls.clear()
    result=pipe.run(None,folder=folder,render_quality='m')
    assert result['status']=='completed' and qualities==['h','m']
    assert [c for c in client.calls if 'candidate' in c]==['006-scene-candidate.json']
    assert 'delivery.json' in result['stages']['scene']['hashes']
    client.calls.clear();pipe.run(None,folder=folder)
    assert qualities[-1]=='m' and not any('candidate' in c for c in client.calls)

@pytest.mark.parametrize('code',['import os\n'+SOURCE,SOURCE+'\nopen("x")',SOURCE+'\neval("x")'])
def test_scene_static_screen_rejects_file_or_dynamic_execution(code):
    with pytest.raises(ValueError):validate_source(code)

def test_invalid_citations_fail_closed(tmp_path):
    class BadSDK(FakeSDK):
        def call(self,prompt,**kw):
            result=super().call(prompt,**kw)
            if isinstance(result,Assessment):result.evidence=['made-up.txt']
            return result
    with pytest.raises(RuntimeError,match='outside'):
        Pipeline(BadSDK(),tmp_path,fake_render,prober=fake_probe).run(Request(prompt='Explain topology'))



def test_audit_cannot_mutate_supplied_evidence(tmp_path):
    class MutatingSDK(FakeSDK):
        def call(self,prompt,**kw):
            result=super().call(prompt,**kw)
            if kw['schema'] is Assessment:
                (kw['cwd']/result.evidence[0]).write_text('changed',encoding='utf-8')
            return result
    with pytest.raises(RuntimeError,match='Evidence changed'):
        Pipeline(MutatingSDK(),tmp_path,fake_render,prober=fake_probe).run(Request(prompt='Explain topology'))

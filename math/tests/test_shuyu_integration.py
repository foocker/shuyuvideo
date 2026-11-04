import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import shuyu_astra as app
from astra import client, runtime
from astra.models import Artifact


def test_prepare_freezes_theme_uses_chosen_delivery_and_does_not_call_models(tmp_path, monkeypatch):
    monkeypatch.setattr(client.CodexSDK, 'call', lambda *a, **kw: pytest.fail('prepare must be offline'))
    folder = app.prepare('Explain homeomorphisms and their hypotheses.', quality='h', output=tmp_path / 'run')
    request = json.loads((folder / 'request.json').read_text(encoding='utf-8'))
    context = json.loads((folder / 'shuyu-context.json').read_text(encoding='utf-8'))
    tokens = json.loads((folder / 'style-tokens.json').read_text(encoding='utf-8'))
    assert tokens['colors']['background'] == '#F4F2EC'
    assert tokens['colors']['ink'] in request['prompt']
    assert context['delivery'] == {'width': 1920, 'height': 1080, 'fps': 30}
    assert 'review_mode' not in request and 'review_mode' not in context
    assert context['auth_mode'] == 'api'
    assert context['style_sha256'] == app.sha(app.PROJECT / 'style/tokens.json')
    expression = context['expression_guidance']
    if not (app.PROJECT / 'studies/production-guide.md').is_file():
        # Fresh clone: studies/ is local only; covered by the next-but-one test.
        assert expression['status'] == 'unavailable'
        return
    assert expression['sha256'] == app.sha(folder / expression['snapshot'])
    assert expression['sha256'] == app.sha(app.PROJECT / expression['source'])
    assert (folder / expression['snapshot']).read_text(encoding='utf-8') in request['prompt']
    with pytest.raises(ValueError):
        app.prepare('Do not overwrite an existing project.', output=folder)


def test_bridge_receives_explicit_auth_without_secret_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('SHUYU_ASTRA_LOGIN_METHOD', 'api')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-secret')
    monkeypatch.setenv('GH_TOKEN', 'test-token')
    monkeypatch.setattr(runtime, 'runtime_directory', lambda: tmp_path)
    artifact = Artifact(summary='test', content='checked', checks=[], sources=[])
    def invoke(args, **kwargs):
        payload = json.loads(kwargs['input'])
        assert payload['authMode'] == 'api' and payload['sandbox'] == 'read-only'
        assert 'OPENAI_API_KEY' not in kwargs['env'] and 'GH_TOKEN' not in kwargs['env']
        assert 'test-secret' not in kwargs['input']
        Path(payload['output']).write_text(artifact.model_dump_json(), encoding='utf-8')
        return SimpleNamespace(returncode=0, stdout='{}', stderr='')
    monkeypatch.setattr(client.subprocess, 'run', invoke)
    actual = client.CodexSDK().call('Check this claim', cwd=tmp_path,
                                  output=tmp_path / 'result.json', schema=Artifact)
    assert actual == artifact


@pytest.mark.parametrize('review,verified,defects,expected', [
    ('astra_only', False, ['Unreadable formula'], 'needs_revision'),
    ('astra_only', True, [], 'astra_reviewed_preview'),
    ('not_reviewed', True, [], 'rendered_not_reviewed'),
])
def test_completed_render_is_not_automatically_approved(tmp_path, monkeypatch, review, verified, defects, expected):
    folder = app.prepare('Explain a precise mathematical statement.', output=tmp_path / 'run')
    (folder / 'attempts').mkdir()
    video = folder / 'film.mp4'
    video.write_bytes(b'test video')
    app.save(folder / 'manifest.json', {'status': 'completed', 'video': 'film.mp4',
                                      'video_sha256': app.sha(video), 'review_status': review})
    app.save(folder / 'attempts/005-render-astra-audit.json', {'verified': verified, 'defects': defects})
    monkeypatch.setattr(app.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout='{"streams":[]}'))
    assert app.export_handoff(folder)['status'] == expected
    video.write_bytes(b'changed video')
    with pytest.raises(ValueError, match='hash'):
        app.export_handoff(folder)


def test_copied_module_is_independent_of_sibling_checkout():
    assert Path(client.__file__).resolve().is_relative_to(app.HERE)
    assert Path(runtime.__file__).resolve().is_relative_to(app.HERE)
    assert app.PROJECT.name == 'shuyuvideo'


def test_default_run_is_owned_by_project_output(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'output_dir', lambda project, kind: tmp_path / project / kind)
    folder = app.prepare('Explain a precise mathematical statement.', project='lesson-a')
    assert folder.parent == tmp_path / 'lesson-a/math'
    context = json.loads((folder / 'shuyu-context.json').read_text(encoding='utf-8'))
    assert context['project'] == 'lesson-a'


def test_resume_avoids_render_directory_left_by_interrupted_worker(tmp_path):
    from test_astra import FakeSDK, fake_probe, fake_render
    from astra.models import Request
    from astra.pipeline import Pipeline
    pipe = Pipeline(FakeSDK(), tmp_path, fake_render, prober=fake_probe)
    result = pipe.run(Request(prompt='Explain a compact mathematical example.'))
    folder = Path(result['run_dir'])
    # A killed renderer can leave a directory before recording an event/audit.
    retained = folder / 'renders/020'
    retained.mkdir()
    marker = retained / 'keep.txt'
    marker.write_text('interrupted evidence', encoding='utf-8')
    resumed = pipe.run(None, folder=folder)
    assert resumed['status'] == 'completed'
    assert (folder / 'renders/021/film.mp4').is_file()
    assert marker.read_text(encoding='utf-8') == 'interrupted evidence'


def test_narration_clock_is_frozen_into_the_request_and_checked_on_export(tmp_path, monkeypatch):
    clock = tmp_path / 'anchors.resolved.json'
    clock.write_text(json.dumps({'flip': 21.485, 'formulaIn': 0.702, 'end': 52.36}), encoding='utf-8')
    folder = app.prepare('Explain the staircase sum formula.', output=tmp_path / 'run', clock=clock)
    request = json.loads((folder / 'request.json').read_text(encoding='utf-8'))
    assert '口播时钟' in request['prompt'] and '21.485' in request['prompt']
    frozen = json.loads((folder / 'narration-clock.json').read_text(encoding='utf-8'))
    assert list(frozen) == ['formulaIn', 'flip', 'end']
    (folder / 'attempts').mkdir()
    video = folder / 'film.mp4'
    video.write_bytes(b'test video')
    app.save(folder / 'manifest.json', {'status': 'completed', 'video': 'film.mp4',
                                      'video_sha256': app.sha(video), 'review_status': 'astra_only'})
    app.save(folder / 'attempts/005-render-astra-audit.json', {'verified': True, 'defects': []})
    for duration, status in (('52.1', 'astra_reviewed_preview'), ('40.0', 'needs_revision')):
        media = json.dumps({'streams': [], 'format': {'duration': duration}})
        monkeypatch.setattr(app.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout=media))
        assert app.export_handoff(folder)['status'] == status
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'flip': 1.0}), encoding='utf-8')
    with pytest.raises(ValueError, match='end'):
        app.prepare('Explain the staircase sum formula.', output=tmp_path / 'run2', clock=bad)


def test_prepare_works_without_the_local_research_library(tmp_path, monkeypatch):
    # studies/ is git-ignored; a fresh clone has only style/ and math/.
    project = tmp_path / 'clone'
    (project / 'style').mkdir(parents=True)
    (project / 'style/tokens.json').write_bytes((app.PROJECT / 'style/tokens.json').read_bytes())
    monkeypatch.setattr(app, 'PROJECT', project)
    folder = app.prepare('Explain homeomorphisms and their hypotheses.', output=tmp_path / 'run')
    request = json.loads((folder / 'request.json').read_text(encoding='utf-8'))
    context = json.loads((folder / 'shuyu-context.json').read_text(encoding='utf-8'))
    assert context['expression_guidance']['status'] == 'unavailable'
    assert not (folder / 'expression-guidance.md').exists()
    assert '本次表达参考' not in request['prompt']

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

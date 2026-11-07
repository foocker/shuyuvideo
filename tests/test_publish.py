import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'publish'))
import publishing
from platforms import bilibili


def valid_spec():
    data = bilibili.template('数学中的光滑', {'homepage': 'https://space.bilibili.com/1', 'name': ''})
    data.update(tags=['数学', '科普'], description='从导数到光滑结构。')
    data['creation_declaration']['label'] = '测试中已核对的选项'
    data['category'] = {'path': ['知识', '科学科普'], 'verified': True}
    data['more_settings'] = [{'label': '测试选项', 'action': 'keep', 'value': None}]
    return data


class BilibiliMetadataTests(unittest.TestCase):
    def test_lengths_tags_and_repost_source(self):
        for key, value in [('title', '字' * 81), ('description', '字' * 2001),
                           ('title', '😀' * 41), ('tags', []), ('tags', ['数学'] * 2),
                           ('tags', [str(i) for i in range(11)]), ('tags', ['数学,科普']),
                           ('copyright', 'repost')]:
            with self.subTest(key=key, value=str(value)[:30]):
                data = valid_spec()
                data[key] = value
                self.assertTrue(bilibili.validate(data)['errors'])
        data = valid_spec()
        data.update(title='字' * 80, description='字' * 2000)
        self.assertEqual(bilibili.validate(data)['errors'], [])

    def test_schedule_bounds_and_expiry_independent_of_host_timezone(self):
        now = datetime(2026, 11, 7, 12, tzinfo=bilibili.SHANGHAI)
        data = valid_spec()
        for delay, valid in [(timedelta(minutes=4, seconds=59), False),
                             (timedelta(minutes=5), True), (timedelta(days=15), True),
                             (timedelta(days=15, seconds=1), False)]:
            data['schedule'] = (now + delay).isoformat()
            self.assertEqual(not bilibili.validate(data, now)['errors'], valid)
        data['schedule'] = (now + timedelta(minutes=10)).isoformat()
        self.assertFalse(bilibili.validate(data, now)['errors'])
        self.assertTrue(bilibili.validate(data, now + timedelta(minutes=6))['errors'])
        for value in ['2026-11-08T12:00:00', '2026-11-08T12:00:00+00:00', 'tomorrow']:
            data['schedule'] = value
            self.assertTrue(bilibili.validate(data, now)['errors'])

    def test_unknown_browser_options_remain_pending(self):
        data = valid_spec()
        data['creation_declaration']['label'] = None
        data['category']['verified'] = False
        data['more_settings'][0]['action'] = 'review'
        result = bilibili.validate(data)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['review']), 3)

    def test_invalid_nested_values_are_reported(self):
        for key in ('account', 'category', 'creation_declaration', 'tags', 'topics', 'commercial', 'more_settings'):
            data = valid_spec()
            data[key] = 123
            self.assertTrue(bilibili.validate(data)['errors'], key)
        data = valid_spec()
        data['account']['homepage'] = 'https://space.bilibili.com.evil.example/1'
        self.assertTrue(bilibili.validate(data)['errors'])


class PublishPacketTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.source = self.base / 'film'
        self.source.mkdir()
        self.target = self.base / 'output/publish/bilibili'
        self.files = {'source': self.source, 'shared': self.source / 'publish/video.json',
                      'metadata': self.source / 'publish/bilibili.json', 'output': self.target,
                      'manifest': self.target / 'packet.json'}
        self.media = {'movie': self.base / 'video.mp4', 'cover': self.base / 'cover.jpg'}
        # Media measurements belong to the cover module; these bytes test approval binding.
        self.media['movie'].write_bytes(b'validated video')
        self.media['cover'].write_bytes(b'validated cover')
        for name, kwargs in [('paths', {'return_value': self.files})]:
            p = patch.object(publishing, name, **kwargs)
            p.start()
            self.addCleanup(p.stop)
        for name, kwargs in [('paths', {'return_value': self.media}),
                             ('check_delivery', {'side_effect': self.delivery})]:
            p = patch.object(publishing.cover, name, **kwargs)
            p.start()
            self.addCleanup(p.stop)
        publishing.write(self.files['shared'], {'schema': 'shuyu-publish-video/v1',
                         'project': 'film', 'approval': None, 'final_action': 'user'})
        self.spec = valid_spec()
        self.save()

    def delivery(self, project):
        return {key: {'sha256': publishing.digest(self.media['movie' if key == 'video' else key])}
                for key in ('video', 'cover')}

    def save(self):
        publishing.write(self.files['metadata'], self.spec)

    def approve(self):
        publishing.approve('film', 'bilibili', '用户明确认可本次测试成片')

    def test_actual_packet_preserves_text_and_does_not_copy_video(self):
        self.approve()
        self.spec['description'] = '第一行。\n第二行，保留换行。'
        self.save()
        publishing.build('film', 'bilibili')
        result = publishing.check('film', 'bilibili', ready=True)
        self.assertTrue(result['ready_for_handoff'])
        self.assertEqual((self.target / 'description.txt').read_text(encoding='utf-8'), self.spec['description'])
        self.assertFalse(list(self.target.glob('*.mp4')))
        self.assertEqual(publishing.read(self.files['manifest'])['state'], 'local_prepared')

    def test_unapproved_and_changed_assets_require_real_confirmation(self):
        with self.assertRaisesRegex(ValueError, '尚未记录'):
            publishing.build('film', 'bilibili')
        self.approve()
        publishing.build('film', 'bilibili')
        for name in ('movie', 'cover'):
            self.media[name].write_bytes(b'updated asset')
            with self.assertRaisesRegex(ValueError, '旧的成片确认失效'):
                publishing.check('film', 'bilibili')
            self.approve()
            publishing.build('film', 'bilibili')

    def test_changed_metadata_or_generated_files_rejected(self):
        self.approve()
        publishing.build('film', 'bilibili')
        self.spec['title'] = '更改后的标题'
        self.save()
        with self.assertRaisesRegex(ValueError, '发布资料'):
            publishing.check('film', 'bilibili')
        publishing.build('film', 'bilibili')
        (self.target / 'title.txt').write_text('旧标题', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'title.txt'):
            publishing.check('film', 'bilibili')
        publishing.build('film', 'bilibili')
        (self.target / 'cover.jpg').unlink()
        with self.assertRaisesRegex(ValueError, 'cover.jpg'):
            publishing.check('film', 'bilibili')

    def test_packet_tampering_and_pending_handoff_rejected(self):
        self.approve()
        self.spec['category']['verified'] = False
        self.save()
        publishing.build('film', 'bilibili')
        self.assertFalse(publishing.check('film', 'bilibili')['ready_for_handoff'])
        with self.assertRaisesRegex(ValueError, '仍需网页核对'):
            publishing.check('film', 'bilibili', ready=True)
        data = publishing.read(self.files['manifest'])
        data['fields']['标题'] = '恶意替换'
        publishing.write(self.files['manifest'], data)
        with self.assertRaisesRegex(ValueError, '字段与配置不同'):
            publishing.check('film', 'bilibili')

    def test_init_does_not_replace_user_draft(self):
        before = self.files['metadata'].read_bytes()
        with self.assertRaisesRegex(ValueError, '已存在'):
            publishing.init('film', 'bilibili')
        self.assertEqual(self.files['metadata'].read_bytes(), before)

    def test_html_escapes_editorial_text(self):
        html = publishing.render_html('</h1><script>alert(1)</script>', [('标题', '</textarea><script>bad()</script>')], [])
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('<script>bad()</script>', html)
        self.assertIn('&lt;/textarea&gt;', html)


if __name__ == '__main__':
    unittest.main()

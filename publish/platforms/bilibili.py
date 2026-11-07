"""Bilibili metadata for assisted browser submission, with no publish operation."""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

UPLOAD_URL = 'https://member.bilibili.com/platform/upload/video/frame'
SHANGHAI = timezone(timedelta(hours=8), 'Asia/Shanghai')


def template(title, account=None):
    return {
        'schema': 'shuyu-publish-bilibili/v1', 'title': title,
        'account': account or {'homepage': '', 'name': ''},
        'copyright': 'original', 'source': '',
        'creation_declaration': {'label': None, 'note': ''},
        'category': {'path': [], 'verified': False},
        'tags': [], 'description': '', 'topics': [],
        'schedule': None, 'collection': None,
        'commercial': {'enabled': False, 'details': ''},
        'more_settings': [
            {'label': label, 'action': 'review', 'value': None}
            for label in ('声明与权益', '视频元素', '互动管理')
        ],
    }


def length(text):
    # Browser form counters may count UTF-16 units. Use the conservative bound.
    return len(text.encode('utf-16-le')) // 2


def validate(data, now=None):
    errors, review = [], []
    if not isinstance(data, dict) or data.get('schema') != 'shuyu-publish-bilibili/v1':
        return {'errors': ['B 站发布配置格式不正确'], 'review': []}

    def text(key, maximum=None, required=False):
        value = data.get(key)
        if not isinstance(value, str) or (required and not value.strip()):
            errors.append(f'{key} 必须是' + ('非空' if required else '') + '文本')
        elif maximum and length(value) > maximum:
            errors.append(f'{key} 超过 {maximum} 字符')
        return value if isinstance(value, str) else ''

    title = text('title', 80, True)
    description = text('description', 2000)
    if '\n' in title or '\r' in title:
        errors.append('标题不能换行')
    if not description.strip():
        review.append('简介尚未填写')
    account = data.get('account')
    if not isinstance(account, dict):
        errors.append('account 必须是对象')
    elif not account.get('homepage'):
        review.append('确认 B 站发布账号')
    else:
        url = urlsplit(str(account['homepage']))
        if url.scheme != 'https' or url.netloc != 'space.bilibili.com' or not url.path.strip('/').isdigit():
            errors.append('账号主页应为 https://space.bilibili.com/<UID>')

    if data.get('copyright') not in ('original', 'repost'):
        errors.append('copyright 只能为 original 或 repost')
    if data.get('copyright') == 'repost' and not str(data.get('source', '')).strip():
        errors.append('转载稿必须填写来源')
    declaration = data.get('creation_declaration')
    if not isinstance(declaration, dict):
        errors.append('creation_declaration 必须是对象')
    elif not isinstance(declaration.get('label'), str) or not declaration['label'].strip():
        review.append('按实际制作方式和网页选项填写创作声明')

    category = data.get('category')
    if not isinstance(category, dict) or not isinstance(category.get('path'), list):
        errors.append('category.path 必须是分区名称数组')
    elif any(not isinstance(x, str) or not x.strip() for x in category['path']):
        errors.append('分区名称不能为空')
    elif not category['path'] or category.get('verified') is not True:
        review.append('在网页核对分区名称与层级')

    tags = data.get('tags')
    if not isinstance(tags, list) or not 1 <= len(tags) <= 10:
        errors.append('标签须填写 1–10 个')
    elif any(not isinstance(x, str) or not x.strip() or x != x.strip() or any(c in x for c in '\n\r,，#') for x in tags):
        errors.append('每个标签须为独立名称，不含 #、逗号、换行或首尾空格')
    elif len({x.casefold() for x in tags}) != len(tags):
        errors.append('标签不能重复')
    topics = data.get('topics')
    if not isinstance(topics, list) or any(not isinstance(x, str) or not x.strip() for x in topics):
        errors.append('topics 必须是话题名称数组')
    elif topics:
        review.append('核对参与话题仍有效且与本片相关')

    schedule = data.get('schedule')
    if schedule is not None:
        try:
            at = datetime.fromisoformat(schedule)
            if at.utcoffset() != timedelta(hours=8):
                raise ValueError('missing Shanghai offset')
            current = now or datetime.now(SHANGHAI)
            if current.tzinfo is None:
                raise ValueError('now must have a timezone')
            delay = at - current
            if not timedelta(minutes=5) <= delay <= timedelta(days=15):
                errors.append('定时发布须距当前时间至少 5 分钟、至多 15 天')
        except (TypeError, ValueError):
            errors.append('schedule 须为含 +08:00 时区的 ISO 时间，或 null')
    collection = data.get('collection')
    if collection is not None:
        if not isinstance(collection, str) or not collection.strip():
            errors.append('collection 须为已有合集名称，或 null')
        else:
            review.append('确认账号拥有合集权限且目标合集存在')
    commercial = data.get('commercial')
    if not isinstance(commercial, dict) or type(commercial.get('enabled')) is not bool:
        errors.append('commercial.enabled 必须是布尔值')
    elif commercial['enabled']:
        if not str(commercial.get('details', '')).strip():
            errors.append('商业推广需填写具体信息')
        review.append('核对商业推广信息及平台对应设置')
    settings = data.get('more_settings')
    if not isinstance(settings, list):
        errors.append('more_settings 必须是设置数组')
    else:
        for item in settings:
            if (not isinstance(item, dict) or not isinstance(item.get('label'), str)
                    or not item['label'].strip() or item.get('action') not in ('review', 'keep', 'set')):
                errors.append('更多设置须填写 label 和 action（review/keep/set）')
            elif item['action'] == 'review':
                review.append(f'查看更多设置：{item["label"]}')
            elif item['action'] == 'set' and item.get('value') is None:
                errors.append(f'更多设置未填写目标值：{item["label"]}')
    return {'errors': errors, 'review': review,
            'lengths': {'title': length(title), 'description': length(description)}}


def fields(data):
    """Ordered browser-fill values. Nulls remain explicit, never guessed."""
    return [
        ('账号主页', data['account'].get('homepage', '')),
        ('标题', data['title']),
        ('稿件类型', '自制' if data['copyright'] == 'original' else '转载'),
        ('转载来源', data.get('source', '')),
        ('创作声明', data['creation_declaration'].get('label') or '待查看网页选项'),
        ('制作方式说明', data['creation_declaration'].get('note', '')),
        ('分区', ' / '.join(data['category']['path']) or '待选择'),
        ('标签', '\n'.join(data['tags'])), ('简介', data['description']),
        ('参与话题', '\n'.join(data['topics']) or '不参加'),
        ('定时发布', data['schedule'] or '不启用定时，用户手动发布'),
        ('加入合集', data['collection'] or '不加入'),
        ('商业推广', data['commercial']['details'] if data['commercial']['enabled'] else '无'),
        *[(item['label'], {'review': '待查看', 'keep': '保留已查看的当前值',
                          'set': str(item.get('value'))}[item['action']]) for item in data['more_settings']],
    ]

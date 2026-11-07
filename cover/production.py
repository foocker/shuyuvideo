"""Offline cover composition and paired video/image delivery. Never calls a model."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps, __version__ as pillow_version

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workspace import ROOT, font_path, font_record, inside, output_dir, project_config


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def paths(project):
    record = project_config(project)
    name = record.get('video', project + '.mp4')
    if Path(name).name != name or '/' in name or '\\' in name or Path(name).suffix.lower() != '.mp4':
        raise ValueError('workspace video must be an MP4 filename without directories')
    movie = output_dir(project, 'renders') / name
    return {
        'source': inside(record['source']), 'movie': movie,
        'cover': movie.with_name(movie.stem + '-cover.jpg'),
        'thumbnail': output_dir(project, 'reports', 'cover-mobile.jpg'),
        'report': output_dir(project, 'reports', 'cover-check.json'),
        'delivery': output_dir(project, 'delivery.json'),
    }


def required(record):
    """Films require covers; brand stings and technical examples remain independent."""
    return inside(record['source']).is_relative_to(ROOT / 'films')


def local_file(source, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError('cover image must be a project-relative local filename')
    path = (source / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(source.resolve()):
        raise ValueError('cover image must stay inside the project source directory')
    if not path.is_file():
        raise ValueError(f'Cover image missing: {path}')
    return path


def integers(values, count, label):
    if not isinstance(values, list) or len(values) != count or any(type(v) is not int for v in values):
        raise ValueError(f'{label} must contain {count} integers')
    return values


def color(value):
    try:
        return ImageColor.getrgb(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f'Invalid cover color: {value}') from exc


def compose(source):
    """Validate all inputs and text geometry before writing any delivery files."""
    config_path = source / 'cover.json'
    if not config_path.is_file():
        raise ValueError(f'Missing {config_path}; design the cover with cover/SKILL.md before rendering')
    spec = json.loads(config_path.read_text(encoding='utf-8'))
    if not isinstance(spec, dict) or spec.get('schema') != 'shuyu-cover/v1':
        raise ValueError('cover.json schema must be shuyu-cover/v1')
    if not isinstance(spec.get('title'), str) or not spec['title'].strip():
        raise ValueError('cover.json needs the film title')
    size = integers(spec.get('size', [1920, 1080]), 2, 'size')
    if any(not 64 <= v <= 8192 for v in size):
        raise ValueError('cover dimensions must be between 64 and 8192 pixels')
    mode = spec.get('mode', 'compose')
    if mode not in ('compose', 'ready'):
        raise ValueError('cover mode must be compose or ready')
    snapshot = {'config': digest(config_path), 'renderer': digest(Path(__file__)),
                'pillow': pillow_version, 'fonts': {}}
    canvas = Image.new('RGB', tuple(size), color(spec.get('background', '#F4F2EC')))
    if spec.get('image'):
        image_path = local_file(source, spec['image'])
        provenance = spec.get('provenance', {})
        if not isinstance(provenance, dict) or any(
                not isinstance(provenance.get(key), str) or not provenance[key].strip()
                for key in ('kind', 'source', 'license')):
            raise ValueError('Image requires provenance.kind, source and license in cover.json')
        snapshot['image'] = {'path': spec['image'], 'sha256': digest(image_path)}
        with Image.open(image_path) as original:
            original.load()
            picture = ImageOps.exif_transpose(original).convert('RGBA')
        fit = spec.get('fit', 'exact')
        if fit == 'exact':
            if picture.width * size[1] != picture.height * size[0]:
                raise ValueError('Image aspect ratio differs; choose fit: cover or contain explicitly')
            picture = picture.resize(tuple(size), Image.Resampling.LANCZOS)
        elif fit == 'cover':
            picture = ImageOps.fit(picture, tuple(size), method=Image.Resampling.LANCZOS)
        elif fit == 'contain':
            picture = ImageOps.contain(picture, tuple(size), method=Image.Resampling.LANCZOS)
        else:
            raise ValueError('fit must be exact, cover or contain')
        canvas.paste(picture, ((size[0] - picture.width) // 2, (size[1] - picture.height) // 2), picture)
    elif mode == 'ready':
        raise ValueError('ready mode requires a finished cover image')
    texts = spec.get('texts', [])
    if not isinstance(texts, list) or (mode == 'compose' and not texts):
        raise ValueError('compose mode requires text layers')
    if mode == 'ready' and texts:
        raise ValueError('ready mode uses the finished image; remove text layers or use compose')
    layout = []
    draw = ImageDraw.Draw(canvas)
    for index, layer in enumerate(texts):
        label = f'texts[{index}]'
        if not isinstance(layer, dict) or not isinstance(layer.get('text'), str) or not layer['text'].strip():
            raise ValueError(f'{label} needs non-empty text')
        x, y, width, height = integers(layer.get('box'), 4, label + '.box')
        if min(x, y) < 0 or min(width, height) <= 0 or x + width > size[0] or y + height > size[1]:
            raise ValueError(f'{label} box is outside the cover')
        font_size = layer.get('fontSize', 80)
        if type(font_size) is not int or not 1 <= font_size <= 2048:
            raise ValueError(f'{label} fontSize must be an integer from 1 to 2048')
        alias = layer.get('font', 'sans-bold')
        try:
            path = font_path(alias)
            record = font_record(alias)
        except KeyError as exc:
            raise ValueError(f'{label}: font {alias!r} is not registered') from exc
        font = ImageFont.truetype(str(path), font_size, index=record.get('faceIndex', 0))
        if alias not in snapshot['fonts']:
            snapshot['fonts'][alias] = {'sha256': digest(path), 'faceIndex': record.get('faceIndex', 0)}
        spacing = layer.get('spacing', 12)
        if type(spacing) is not int or spacing < 0:
            raise ValueError(f'{label} spacing must be a non-negative integer')
        align = layer.get('align', 'left')
        if align not in ('left', 'center', 'right'):
            raise ValueError(f'{label} align must be left, center or right')
        bounds = draw.multiline_textbbox((0, 0), layer['text'], font=font, spacing=spacing, align=align)
        tw, th = bounds[2] - bounds[0], bounds[3] - bounds[1]
        if tw > width or th > height:
            raise ValueError(f'{label} text overflows its box ({tw}x{th} > {width}x{height}); shorten or re-layout')
        offset = 0 if align == 'left' else (width - tw) / 2 if align == 'center' else width - tw
        draw.multiline_text((x + offset - bounds[0], y - bounds[1]), layer['text'], font=font,
                            fill=color(layer.get('color', '#183D37')), spacing=spacing, align=align)
        layout.append({'text': layer['text'], 'bounds': [x + offset, y, x + offset + tw, y + th]})
    return canvas, snapshot, layout, spec['title']


def preflight(project):
    compose(paths(project)['source'])


def build(project):
    files = paths(project)
    canvas, snapshot, layout, title = compose(files['source'])
    files['cover'].parent.mkdir(parents=True, exist_ok=True)
    temporary = files['cover'].with_suffix('.tmp.jpg')
    canvas.save(temporary, format='JPEG', quality=95, subsampling=0)
    temporary.replace(files['cover'])
    files['thumbnail'].parent.mkdir(parents=True, exist_ok=True)
    # Thumbnail is decoded from the actual deliverable, including JPEG compression.
    with Image.open(files['cover']) as decoded:
        decoded.resize((360, round(360 * decoded.height / decoded.width)),
                       Image.Resampling.LANCZOS).save(files['thumbnail'], quality=95)
    report = {'schema': 'shuyu-cover-check/v1', 'ok': True, 'project': project, 'title': title,
              'size': list(canvas.size), 'inputs': snapshot, 'sha256': digest(files['cover']), 'layout': layout,
              'scope': 'Local inputs, geometry and file integrity only. Review artwork and mobile readability separately.'}
    write_json(files['report'], report)
    return report


def check(project):
    files = paths(project)
    canvas, snapshot, _, _ = compose(files['source'])
    if not files['report'].is_file() or not files['cover'].is_file():
        raise ValueError(f'Cover has not been built; run shuyu cover build {project}')
    report = json.loads(files['report'].read_text(encoding='utf-8'))
    if (not isinstance(report, dict) or report.get('schema') != 'shuyu-cover-check/v1'
            or report.get('project') != project or report.get('ok') is not True):
        raise ValueError('Cover report is invalid; rebuild it')
    if report.get('inputs') != snapshot:
        raise ValueError('Cover inputs changed; rebuild the cover and review it again')
    if report.get('sha256') != digest(files['cover']):
        raise ValueError('Cover file differs from its build report; rebuild it')
    with Image.open(files['cover']) as image:
        image.load()
        if image.size != canvas.size or image.format != 'JPEG':
            raise ValueError('Cover format or dimensions differ from the specification')
    return report


def invalidate_delivery(project):
    paths(project)['delivery'].unlink(missing_ok=True)


def file_record(path, base):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f'Delivery file missing or empty: {path}')
    return {'path': path.relative_to(base).as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)}


def package_delivery(project, measurement):
    """Called only after render_check succeeded; binds the measured video to its cover."""
    files = paths(project)
    if measurement.get('ok') is not True:
        raise ValueError('Video measurement failed; cannot package delivery')
    cover_report = check(project)
    report = {'schema': 'shuyu-delivery/v1', 'project': project, 'title': cover_report['title'],
              'createdAt': datetime.now(timezone.utc).isoformat(),
              'video': file_record(files['movie'], files['delivery'].parent),
              'cover': file_record(files['cover'], files['delivery'].parent),
              'measurements': measurement, 'coverInputs': cover_report['inputs'],
              'scope': 'Paired file integrity and automated measurements; visual review and listening are recorded in REVIEW.md.'}
    write_json(files['delivery'], report)
    return report


def check_delivery(project):
    files = paths(project)
    cover_report = check(project)
    if not files['delivery'].is_file():
        raise ValueError(f'Delivery manifest missing; run shuyu deliver {project}')
    report = json.loads(files['delivery'].read_text(encoding='utf-8'))
    if (not isinstance(report, dict) or report.get('schema') != 'shuyu-delivery/v1'
            or report.get('project') != project):
        raise ValueError('Delivery manifest belongs to a different schema or project')
    for key, path in [('video', files['movie']), ('cover', files['cover'])]:
        if file_record(path, files['delivery'].parent) != report.get(key):
            raise ValueError(f'Delivery {key} changed; run shuyu deliver again')
    if report.get('coverInputs') != cover_report['inputs']:
        raise ValueError('Delivery references an earlier cover; run shuyu deliver again')
    return report


def deliver(project):
    invalidate_delivery(project)
    files = paths(project)
    if not files['movie'].is_file():
        raise ValueError(f'Render the video first: {files["movie"]}')
    build(project)
    sys.path.insert(0, str(ROOT / 'scripts/validation'))
    from render_check import check as check_video
    errors, summary = check_video(files['movie'], files['source'])
    measurement = {'ok': not errors, 'kind': 'render', 'errors': errors, **summary}
    write_json(output_dir(project, 'reports', 'delivery-video-check.json'), measurement)
    if errors:
        raise ValueError('Video measurement failed: ' + '; '.join(errors))
    return package_delivery(project, measurement)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'check'])
    parser.add_argument('project')
    args = parser.parse_args(argv)
    report = build(args.project) if args.action == 'build' else check(args.project)
    print(json.dumps({'ok': True, 'cover': str(paths(args.project)['cover']),
                      'mobilePreview': str(paths(args.project)['thumbnail']), 'size': report['size']}, ensure_ascii=False))
    return 0


def delivery_main(argv=None):
    parser = argparse.ArgumentParser(description='Deliver an existing MP4 with its independent cover; no video rendering.')
    parser.add_argument('project')
    parser.add_argument('--check', action='store_true', help='Check existing pair and input hashes without rebuilding')
    args = parser.parse_args(argv)
    report = check_delivery(args.project) if args.check else deliver(args.project)
    base = paths(args.project)['delivery'].parent
    print(json.dumps({'ok': True, 'video': str(base / report['video']['path']),
                      'cover': str(base / report['cover']['path']),
                      'manifest': str(paths(args.project)['delivery'])}, ensure_ascii=False))
    return 0

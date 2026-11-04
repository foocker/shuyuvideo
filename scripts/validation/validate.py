"""Validate local asset provenance and primary-shot timeline contracts."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def local_file(root, value):
    if not text(value) or Path(value).is_absolute():
        raise ValueError('path must be non-empty and relative to the manifest')
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'missing file or path outside manifest directory: {value}')
    return path


def assets(document, root):
    errors, warnings = [], []
    if not isinstance(document, dict) or document.get('schema') != 'shuyu-assets/v1':
        return ['schema must be shuyu-assets/v1'], warnings
    items = document.get('assets')
    if not isinstance(items, list):
        return ['assets must be an array (empty is allowed for an asset-free scene)'], warnings
    use = document.get('intendedUse', 'study')
    if use not in ('study', 'commercial'):
        errors.append('intendedUse must be study or commercial')
    ids = set()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f'asset[{i}] must be an object')
            continue
        label = item.get('id')
        if not text(label) or label in ids:
            errors.append(f'asset[{i}]: missing or duplicate id')
        if text(label):
            ids.add(label)
        for key in ('role', 'license', 'source'):
            if not text(item.get(key)):
                errors.append(f'{label}: missing {key}')
        kind = item.get('kind')
        if kind not in ('project-original', 'user-provided', 'external'):
            errors.append(f'{label}: invalid kind')
        # Accept both SPDX-style IDs and ordinary labels such as CC BY-NC 4.0.
        license_id = re.sub(r'[\s_]+', '-', str(item.get('license', '')).strip().upper())
        if license_id in ('UNKNOWN', 'UNSPECIFIED'):
            errors.append(f'{label}: license must be resolved before the asset is marked usable')
        if kind == 'external':
            if license_id == 'PROJECT-INTERNAL':
                errors.append(f'{label}: external assets require their actual license or permission record')
            parsed = urlsplit(str(item.get('source', '')))
            if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                errors.append(f'{label}: external source must be an HTTP(S) URL')
        if license_id.startswith('CC-BY') and not text(item.get('credit')):
            errors.append(f'{label}: this CC license requires a credit record')
        if license_id.startswith('CC-') and '-NC' in license_id and use == 'commercial':
            errors.append(f'{label}: noncommercial asset in a commercial manifest')
        if license_id.startswith('CC-') and '-SA' in license_id:
            if not text(item.get('adaptationLicense')) or not text(item.get('changes')):
                errors.append(f'{label}: ShareAlike asset requires adaptationLicense and changes records')
            warnings.append(f'{label}: check the source ShareAlike obligations; metadata alone does not establish compliance')
        try:
            path = local_file(root, item.get('path'))
            if item.get('sha256') is not None:
                expected = item['sha256']
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if not isinstance(expected, str) or expected.lower() != actual:
                    errors.append(f'{label}: SHA-256 mismatch')
            if item.get('licenseFile') is not None:
                local_file(root, item['licenseFile'])
        except (ValueError, OSError) as exc:
            errors.append(f'{label}: {exc}')
    return errors, warnings


def timeline(document, asset_document=None):
    errors, warnings = [], []
    if not isinstance(document, dict) or document.get('schema') != 'shuyu-timeline/v1':
        return ['schema must be shuyu-timeline/v1'], warnings
    fps, total = document.get('fps'), document.get('durationFrames')
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or not math.isfinite(fps) or fps <= 0:
        errors.append('fps must be a finite positive number')
    if not integer(total) or total <= 0:
        errors.append('durationFrames must be a positive integer')
    overlap = document.get('maxOverlapFrames', 0)
    if not integer(overlap) or overlap < 0:
        errors.append('maxOverlapFrames must be a non-negative integer')
    shots = document.get('shots')
    if not isinstance(shots, list) or not shots:
        errors.append('shots must be a non-empty primary-picture sequence')
    if errors:
        return errors, warnings
    ids, valid = set(), []
    asset_ids = {a['id'] for a in asset_document['assets']} if asset_document is not None else None
    for index, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f'shot[{index}] must be an object')
            continue
        label = shot.get('id')
        if not text(label) or label in ids:
            errors.append(f'shot[{index}]: missing or duplicate id')
            continue
        if text(label):
            ids.add(label)
        for field in ('subject', 'action'):
            if not text(shot.get(field)):
                errors.append(f'{label}: missing {field}')
        start, end = shot.get('startFrame'), shot.get('endFrame')
        if not integer(start) or not integer(end) or not 0 <= start < end <= total:
            errors.append(f'{label}: invalid frame interval')
            continue
        reading = shot.get('readFrames', 0)
        if not integer(reading) or not 0 <= reading <= end - start:
            errors.append(f'{label}: readFrames must fit within the shot')
        refs = shot.get('assets', [])
        if not isinstance(refs, list) or not all(text(ref) for ref in refs):
            errors.append(f'{label}: assets must be an array of IDs')
        elif asset_ids is not None:
            errors.extend(f'{label}: unknown asset {ref}' for ref in refs if ref not in asset_ids)
        elif refs:
            errors.append(f'{label}: supply --assets to verify referenced asset IDs')
        valid.append(shot)
    coverage = 0
    for shot in sorted(valid, key=lambda s: (s['startFrame'], s['endFrame'])):
        start, end, label = shot['startFrame'], shot['endFrame'], shot['id']
        if start > coverage:
            errors.append(f'{label}: uncovered frames {coverage}..{start}')
        if coverage - start > overlap:
            errors.append(f'{label}: overlap exceeds {overlap} frames')
        coverage = max(coverage, end)
    if coverage != total:
        errors.append(f'coverage ends at {coverage}, expected {total}')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('assets', 'timeline'))
    parser.add_argument('input', type=Path)
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.input.read_text(encoding='utf-8'))
        asset_doc, pre_errors, pre_warnings = None, [], []
        if args.assets:
            asset_doc = json.loads(args.assets.read_text(encoding='utf-8'))
            pre_errors, pre_warnings = assets(asset_doc, args.assets.parent)
        if pre_errors:
            errors, warnings = pre_errors, pre_warnings
        elif args.kind == 'assets':
            errors, warnings = assets(document, args.input.parent)
        else:
            errors, warnings = timeline(document, asset_doc)
            warnings = pre_warnings + warnings
    except (OSError, ValueError, TypeError) as exc:
        errors, warnings = [str(exc)], []
    report = {'ok': not errors, 'kind': args.kind, 'errors': errors, 'warnings': warnings,
              'scope': 'Local structure, records and file integrity; not proof of rights or mathematical correctness.'}
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(content + '\n', encoding='utf-8')
    print(content)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

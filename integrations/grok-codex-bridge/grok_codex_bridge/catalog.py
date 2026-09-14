"""Add selected Grok metadata to a native catalog without rewriting native rows."""
import copy
import hashlib
import json
import os
from pathlib import Path

MAX_CATALOG_BYTES = 4 * 1024 * 1024


def read_catalog(path):
    path = Path(path)
    if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
        raise ValueError('Catalog source must be a regular file, not a link/reparse point')
    with path.open('rb') as stream:
        raw = stream.read(MAX_CATALOG_BYTES + 1)
    if len(raw) > MAX_CATALOG_BYTES:
        raise ValueError('Catalog exceeds the 4 MiB bound')
    value = json.loads(raw.decode('utf-8-sig'))
    models(value)
    return value


def models(catalog):
    rows = catalog.get('models') if isinstance(catalog, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError('Catalog must contain a nonempty models list')
    slugs = []
    for row in rows:
        slug = row.get('slug') if isinstance(row, dict) else None
        if not isinstance(slug, str) or not slug:
            raise ValueError('Every catalog row must have a slug')
        slugs.append(slug)
    if len(set(slugs)) != len(slugs):
        raise ValueError('Duplicate model slugs are not accepted')
    return rows


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def extend_native_catalog(native, routed, selected_model):
    """Preserve native fields and append the explicitly selected namespaced rows."""
    native_rows = models(native)
    routed_rows = models(routed)
    selections = [selected_model] if isinstance(selected_model, str) else selected_model
    if not isinstance(selections, list) or not selections:
        raise ValueError('Choose a nonempty, unique Grok model selection')
    if not all(isinstance(item, str) and item.startswith('xai/grok-') for item in selections):
        raise ValueError('Only an explicitly selected xai/grok model can be appended')
    if len(set(selections)) != len(selections):
        raise ValueError('Choose a nonempty, unique Grok model selection')
    if any('/' in row['slug'] for row in native_rows):
        raise ValueError('Native source already contains routed models; choose the native source')
    result = copy.deepcopy(native)
    selected_receipts = []
    for selected in selections:
        matches = [row for row in routed_rows if row['slug'] == selected]
        if len(matches) != 1:
            raise ValueError('Selected Grok model is absent or ambiguous')
        row = matches[0]
        window, limit = row.get('context_window'), row.get('auto_compact_token_limit')
        if (type(window) is not int or window <= 0 or type(limit) is not int
                or not 0 < limit < window):
            raise ValueError('Selected model needs valid context and compaction metadata')
        result['models'].append(copy.deepcopy(row))
        selected_receipts.append({'selected_model': selected, 'selected_model_sha256': digest(row),
                                  'context_window': window, 'auto_compact_token_limit': limit})
    # Do not copy the routed catalog's GPT rows, defaults, timestamps or prompts.
    assert result['models'][:len(native_rows)] == native_rows
    receipt = {'native_rows': len(native_rows), 'native_models_sha256': digest(native_rows),
               'native_rows_unchanged': True}
    if isinstance(selected_model, str):
        receipt.update(selected_receipts[0])  # Preserve the existing one-model contract.
    else:
        receipt.update(selected_models=list(selections), selected_rows=selected_receipts)
    return result, receipt


def refresh_catalog(native_path, routed_path, output_path, selected_model):
    """Refresh only the owned generated file; sources and user config are read-only."""
    output = Path(output_path)
    if output.resolve() in {Path(native_path).resolve(), Path(routed_path).resolve()}:
        raise ValueError('Generated catalog must not overwrite either source')
    result, receipt = extend_native_catalog(read_catalog(native_path), read_catalog(routed_path), selected_model)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and (output.is_symlink() or getattr(output.lstat(), 'st_file_attributes', 0) & 0x400):
        raise ValueError('Generated catalog path must not be a link/reparse point')
    changed = not output.is_file() or output.read_bytes() != raw
    if changed:
        temporary = output.with_name(output.name + f'.{os.getpid()}.tmp')
        with temporary.open('xb') as stream:
            stream.write(raw)
        os.replace(temporary, output)
    receipt.update(output_path=str(output), output_sha256=hashlib.sha256(raw).hexdigest(), changed=changed)
    return receipt

from downloader.db.persistence import get_language_id, get_format_id, get_category_id

_lang_id_by_code = {}
_format_id_by_code = {}
_category_id_by_name = {}


def _load_from_cache(key, cache, query_method):
    if not key in cache:
        id = query_method(key)
        cache[key] = id
    return cache[key]


def cached_language_id(lang_code):
    return _load_from_cache(
        lang_code,
        _lang_id_by_code,
        get_language_id
    )


def cached_format_id(format_code):
    return _load_from_cache(
        format_code,
        _format_id_by_code,
        get_format_id
    )


def cached_category_ids(cat_names):
    return [_load_from_cache(
        name,
        _category_id_by_name,
        get_category_id
    ) for name in cat_names]



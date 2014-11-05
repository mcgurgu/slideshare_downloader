from  persistence import *

_lang_id_by_code = {}
_format_id_by_code = {}
_category_id_by_name = {}

# TODO(vucalur): refactor: DRY

def _load_from_cache(key, cache, query_method, session):
    if not key in cache:
        id = query_method(key, session)
        cache[key] = id
    return cache[key]


# TODO(vucalur): refactor: get rid of passing session
def cached_language_id(lang_code, session):
    return _load_from_cache(
        lang_code,
        _lang_id_by_code,
        get_language_id,
        session
    )


# TODO(vucalur): refactor: get rid of passing session
def cached_format_id(format_code, session):
    return _load_from_cache(
        format_code,
        _format_id_by_code,
        get_format_id,
        session
    )


# TODO(vucalur): refactor: get rid of passing session
def cached_category_ids(cat_names, session):
    return [_load_from_cache(
        name,
        _category_id_by_name,
        get_category_id,
        session
    ) for name in cat_names]



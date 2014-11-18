from downloader.db.persistence import get_or_create_language_id, get_format_id, get_category_id
from downloader.util.logger import log

_lang_id_by_code = {}
_format_id_by_code = {}
_category_id_by_name = {}


def _load_from_cache(key, cache, query_method):
    if not key in cache:
        log.debug("CACHE: key=%s not found in cache=%s" % (key, str(cache)))
        cache[key] = query_method(key)
    else:
        log.debug("CACHE: returning cached value for key=%s" % key)
    return cache[key]


def cached_language_id(lang_code):
    return _load_from_cache(
        lang_code,
        _lang_id_by_code,
        get_or_create_language_id
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



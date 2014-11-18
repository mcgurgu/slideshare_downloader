from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from downloader.config import config_my as config
from downloader.db.model import Format, Type, Category, Base, User, Language
from downloader.util.logger import log


__engine = create_engine('sqlite:///' + config.db_filename)

__session = None


def save_all_and_commit(data):
    __session.add_all(data)
    __session.commit()


def is_user_processed(username):
    sole_username = __session.query(User.username).filter_by(username=username).scalar()
    return sole_username is not None


def _get_id_create_when_necessary(query_select, entity, **query_filter):
    query = __session.query(query_select).filter_by(**query_filter)
    id_ = query.scalar()
    if id_ is not None:
        log.debug("DB: found id=%d for %s(%s)" % (id_, entity.__name__, str(query_filter)))
        return id_
    else:
        log.debug("DB: %s(%s) not found" % (entity.__name__, str(query_filter)))
        new_obj = entity(**query_filter)
        __session.add(new_obj)
        __session.commit()
        log.debug("DB: %s(id=%d, %s) successfully stored" % (entity.__name__, new_obj.id, str(query_filter)))
        return new_obj.id


__lang_id_by_code = {}
__format_id_by_code = {}
__category_id_by_name = {}


def _load_from_cache(key, cache, query_method):
    if not key in cache:
        log.debug("CACHE: key=%s not found in cache=%s" % (key, str(cache)))
        cache[key] = query_method(key)
    else:
        log.debug("CACHE: returning cached value for key=%s" % key)
    return cache[key]


def get_language_id(lang_code):
    return _load_from_cache(
        lang_code,
        __lang_id_by_code,
        lambda code: _get_id_create_when_necessary(Language.id, Language, code=code)
    )


def get_format_id(format_code):
    return _load_from_cache(
        format_code,
        __format_id_by_code,
        lambda code: _get_id_create_when_necessary(Format.id, Format, code=code)
    )


def get_category_ids(cat_names):
    return [_load_from_cache(
        cat_name,
        __category_id_by_name,
        lambda name: _get_id_create_when_necessary(Category.id, Category, name=name)
    ) for cat_name in cat_names]


def _populate_dictionary_tables():
    types = [Type(code=0, name='presentation'),
             Type(code=1, name='document'),
             Type(code=2, name='portfolio'),
             Type(code=3, name='video')]

    save_all_and_commit(types)


DBSession = sessionmaker(bind=__engine)
__session = DBSession()


def __main():
    Base.metadata.create_all(__engine)
    _populate_dictionary_tables()


if __name__ == '__main__':
    __main()

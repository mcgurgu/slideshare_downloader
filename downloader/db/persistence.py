from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from downloader.config import config_my as config
from downloader.db.model import Type, Category, Base, User, Country
from downloader.util.logger import log


__engine = create_engine('sqlite:///' + config.db_filename)

__session = None


def save_all_and_commit(data):
    try:
        __session.add_all(data)
        __session.commit()
    except SQLAlchemyError as e:
        log.exception('Caught SQLAlchemyError %s while committing. Rolling back' % (e.message))
        __session.rollback()


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

# TODO(vucalur): refactor: DRY. Cache method/class wrapper ?
__category_id_by_name = {'': None}
__type_id_by_name = {'': None}
__country_id_by_name = {'': None}


def _load_from_cache(key, cache, query_method):
    if not key in cache:
        log.debug("CACHE: key=%s not found in cache=%s" % (key, str(cache)))
        cache[key] = query_method(key)
    else:
        log.debug("CACHE: returning cached value for key=%s" % key)
    return cache[key]


def get_type_id(type_name):
    return _load_from_cache(
        type_name,
        __type_id_by_name,
        lambda name: _get_id_create_when_necessary(Type.id, Type, name=type_name)
    )


def get_country_id(country_name):
    return _load_from_cache(
        country_name,
        __country_id_by_name,
        lambda name: _get_id_create_when_necessary(Country.id, Country, name=country_name)
    )


def get_category_ids(cat_names):
    return [_load_from_cache(
        cat_name,
        __category_id_by_name,
        lambda name: _get_id_create_when_necessary(Category.id, Category, name=name)
    ) for cat_name in cat_names]


DBSession = sessionmaker(bind=__engine)
__session = DBSession()
Base.metadata.create_all(__engine)


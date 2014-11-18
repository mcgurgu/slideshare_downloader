from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from downloader.config import config_my as config
from downloader.db.model import Format, Type, Category, Base, User, Language
from downloader.util.logger import log


__engine = create_engine('sqlite:///' + config.db_filename)

__session = None


def save_all_and_commit(data):
    __session.add_all(data)
    __session.commit()


def is_user_processed(username):
    query = __session.query(User).filter_by(username=username)
    return query.all() != []


def _get_id_create_when_necessary(query_select, entity, **query_filter):
    query = __session.query(query_select).filter_by(**query_filter)
    try:
        id_ = query.one()[0]
        log.debug("DB: found id=%d for %s(%s)" % (id_, entity.__name__, str(query_filter)))
        return id_
    except NoResultFound:
        log.debug("DB: %s(%s) not found" % (entity, str(query_filter)))
        new_obj = entity(**query_filter)
        __session.add(new_obj)
        __session.commit()
        log.debug("DB: %s(id=%d, %s) successfully stored" % (entity.__name__, new_obj.id, str(query_filter)))
        return new_obj.id


def get_or_create_language_id(lang_code):
    id = _get_id_create_when_necessary(Language.id, Language, code=lang_code)
    return id


def get_format_id(format_code):
    id = _get_id_create_when_necessary(Format.id, Format, code=format_code)
    return id


def get_category_id(cat_name):
    id = _get_id_create_when_necessary(Category.id, Category, name=cat_name)
    return id


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

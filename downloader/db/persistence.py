from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urlparse import urlparse

from downloader.config import config_my as config
from downloader.db.model import Format, Type, Category, Base, User, Language, Slideshow
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


def pq_to_slideshow(slideshow_page_as_pq):
    path_with_ssid = slideshow_page_as_pq('meta.twitter_player')[0].attrib['value']
    return Slideshow(
        id = urlparse(path_with_ssid).path.split('/')[-1],
        title = slideshow_page_as_pq('title')[0].text,
        description = slideshow_page_as_pq('meta[name=description]')[0].attrib['content'],
        url = slideshow_page_as_pq.base_url,
        created_date = slideshow_page_as_pq('meta[name=slideshow_created_at]')[0].attrib['content'],
        updated_date = slideshow_page_as_pq('meta[name=slideshow_updated_at]')[0].attrib['content'],
        # Szymon: Cannot find it on the page; setting fixed value for now
        language_id = 'en',
        # Szymon: Cannot find it on the page; setting fixed value for now
        format_id = 'ppt',
        # Szymon: same as above
        type_code  = 1,
        username = slideshow_page_as_pq('meta[name=slideshow_author]')[0].attrib['content'].split('/')[-1],
        # Szymon: already scrapped in additional user info
        # downloads_count = int(slideshow_page_as_pq('meta[name=slideshow_download_count]')[0].attrib['content']),
        # views_count = int(slideshow_page_as_pq('meta[name=slideshow_view_count]')[0].attrib['content']),
        # embeds_count = int(slideshow_page_as_pq('meta[name=slideshow_embed_count]')[0].attrib['content']),
        comments_count = int(slideshow_page_as_pq('meta[name=slideshow_comment_count]')[0].attrib['content']),
        likes_count = int(slideshow_page_as_pq('meta[name=slideshow_favorites_count]')[0].attrib['content']))



DBSession = sessionmaker(bind=__engine)
__session = DBSession()


def __main():
    Base.metadata.create_all(__engine)
    _populate_dictionary_tables()


if __name__ == '__main__':
    __main()

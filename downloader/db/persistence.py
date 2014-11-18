from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from downloader.config import config_my as config
from downloader.db.model import Format, Type, Category, Base, User, Language


__engine = create_engine('sqlite:///' + config.db_filename)

__session = None


def save_all_and_commit(data):
    __session.add_all(data)
    __session.commit()


def is_user_processed(username):
    query = __session.query(User).filter_by(username=username)
    return query.all() != []


def get_or_create_language_id(lang_code):
    query = __session.query(Language.id).filter_by(code=lang_code)
    try:
        return query.one()[0]
    except NoResultFound:
        new_lang = Language(code=lang_code)
        __session.add(new_lang)
        __session.commit()
        return new_lang.id


# TODO(vucalur): refactor: DRY 1.a
def get_format_id(format_code):
    query = __session.query(Format.id).filter_by(code=format_code)
    return query.one()[0]


# TODO(vucalur): refactor: DRY 1.b
def get_category_id(cat_name):
    query = __session.query(Category.id).filter_by(name=cat_name)
    return query.one()[0]


def _populate_dictionary_tables():
    # TODO(vucalur): these are not all!
    formats = [Format(code='ppt'),
               Format(code='pdf'),
               Format(code='pps'),
               Format(code='odp'),
               Format(code='doc'),
               Format(code='pot'),
               Format(code='txt'),
               Format(code='rdf')]
    types = [Type(code=0, name='presentation'),
             Type(code=1, name='document'),
             Type(code=2, name='portfolio'),
             Type(code=3, name='video')]
    default_category_names = ['Art & Photos', 'Automotive', 'Business', 'Career', 'Data & Analytics', 'Design', 'Devices & Hardware',
                              'Economy & Finance', 'Education', 'Engineering', 'Entertainment & Humor', 'Environment', 'Food',
                              'Government & Nonprofit', 'Health & Medicine', 'Healthcare', 'Internet', 'Investor Relations',
                              'Law', 'Leadership & Management', 'Lifestyle', 'Marketing', 'Mobile', 'News & Politics', 'Presentations & Public Speaking',
                              'Real Estate', 'Recruiting & HR', 'Retail', 'Sales', 'Science', 'Self Improvement', 'Services',
                              'Small Business & Entrepreneurship', 'Social Media', 'Software', 'Spiritual', 'Sports', 'Technology', 'Travel']
    categories = [Category(name=cat) for cat in default_category_names]

    data = formats + types + categories
    save_all_and_commit(data)


DBSession = sessionmaker(bind=__engine)
__session = DBSession()


def __main():
    Base.metadata.create_all(__engine)
    _populate_dictionary_tables()


if __name__ == '__main__':
    __main()

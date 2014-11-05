from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from downloader.config import Config
from downloader.model import Format, Type, Category, Base, User, Language


engine = create_engine('sqlite:///' + Config['db.filename'] + '.db')


def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()


def save_all_and_commit(data, session):
    session.add_all(data)
    session.commit()


def is_user_processed(username, session):
    query = session.query(User).filter_by(username=username)
    return query.all() != []


# TODO(vucalur): refactor: DRY 1.a
def get_language_id(lang_code, session):
    query = session.query(Language.id).filter_by(code=lang_code)
    return query.all()


# TODO(vucalur): refactor: DRY 1.b
def get_format_id(format_code, session):
    query = session.query(Format.id).filter_by(code=format_code)
    return query.all()


# TODO(vucalur): refactor: DRY 1.c
def get_category_id(cat_name, session):
    query = session.query(Category.id).filter_by(name=cat_name)
    return query.all()


def _populate_dictionary_tables(session):
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
    save_all_and_commit(data, session)


if __name__ == '__main__':
    session = get_session()
    Base.metadata.create_all(engine)
    _populate_dictionary_tables(session)

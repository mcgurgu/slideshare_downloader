from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from downloader.config import Config
from downloader.model import Format, SlideshowType, Category, Base


engine = create_engine('sqlite:///' + Config['db.filename'] + '.db')


def get_session():
    DBSession = sessionmaker(bind=engine)
    return DBSession()


def save_all_and_commit(data, session):
    session.add_all(data)
    session.commit()


def _populate_dictionary_tables(session):
    formats = [Format(code='ppt'),
               Format(code='pdf'),
               Format(code='pps'),
               Format(code='odp'),
               Format(code='doc'),
               Format(code='pot'),
               Format(code='txt'),
               Format(code='rdf')]
    slideshowtypes = [SlideshowType(code=0, name='presentation'),
                      SlideshowType(code=1, name='document'),
                      SlideshowType(code=2, name='portfolio'),
                      SlideshowType(code=3, name='video')]
    default_category_names = ['Art & Photos', 'Automotive', 'Business', 'Career', 'Data & Analytics', 'Design', 'Devices & Hardware',
                              'Economy & Finance', 'Education', 'Engineering', 'Entertainment & Humor', 'Environment', 'Food',
                              'Government & Nonprofit', 'Health & Medicine', 'Healthcare', 'Internet', 'Investor Relations',
                              'Law', 'Leadership & Management', 'Lifestyle', 'Marketing', 'Mobile', 'News & Politics', 'Presentations & Public Speaking',
                              'Real Estate', 'Recruiting & HR', 'Retail', 'Sales', 'Science', 'Self Improvement', 'Services',
                              'Small Business & Entrepreneurship', 'Social Media', 'Software', 'Spiritual', 'Sports', 'Technology', 'Travel']
    default_categories = [Category(name=cat) for cat in default_category_names]

    data = formats + slideshowtypes + default_categories
    save_all_and_commit(data, session)


if __name__ == '__main__':
    session = get_session()
    Base.metadata.create_all(engine)
    _populate_dictionary_tables(session)

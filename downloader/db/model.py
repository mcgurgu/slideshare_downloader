from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from downloader.config import config_my as config
from downloader.db.unique_object import unique_constructor


Base = declarative_base()

__engine = create_engine('sqlite:///' + config.db_filename)

Session = scoped_session(sessionmaker(bind=__engine))

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'


class Slideshow(Base):
    __tablename__ = 'slideshow'
    ssid = Column(Integer, primary_key=True)
    # TODO(vucalur): UNICODE support !
    title = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    created_date = Column(DateTime, nullable=False)
    updated_date = Column(DateTime)
    type_id = Column(Integer, ForeignKey('type.id'), nullable=False)
    type = relationship('Type')
    username = Column(String, ForeignKey('user.username'))

    downloads_count = Column(Integer, nullable=False)
    views_on_slideshare_count = Column(Integer, nullable=False)
    views_from_embeds_count = Column(Integer, nullable=False)
    embeds_count = Column(Integer, nullable=False)

    categories = relationship('Category', secondary='slideshow_has_category')

    def __setattr__(self, key, value):
        if key in ['created_date', 'updated_date']:
            super(Slideshow, self).__setattr__(key, datetime.strptime(value, DATETIME_FORMAT))
        else:
            super(Slideshow, self).__setattr__(key, value)


@unique_constructor(Session,
    lambda name: name,
    lambda query, name: query.filter(Type.name == name)
)
class Type(Base):
    __tablename__ = 'type'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class User(Base):
    __tablename__ = 'user'
    follow_network_downloaded = Column(Boolean, nullable=False, default=False)
    username = Column(String, primary_key=True)  # leaving off username (API) as PK
    city = Column(String)
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country')
    organization = Column(String)
    full_name = Column(String)
    description = Column(String)
    joined_date = Column(DateTime, nullable=False)
    url = Column(String)
    about = Column(String)
    works_for = Column(String)
    slideshows = relationship('Slideshow', backref="user")
    tags = relationship('Tag', secondary='user_has_tag')

    def __setattr__(self, key, value):
        if key == 'joined_date':
            super(User, self).__setattr__(key, datetime.strptime(value, DATETIME_FORMAT))
        else:
            super(User, self).__setattr__(key, value)


@unique_constructor(Session,
    lambda name: name,
    lambda query, name: query.filter(Country.name == name)
)
class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


@unique_constructor(Session,
    lambda name: name,
    lambda query, name: query.filter(Category.name == name)
)
class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    slideshows = relationship('Slideshow', secondary="slideshow_has_category")


class SlideshowHasCategory(Base):
    __tablename__ = 'slideshow_has_category'
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), primary_key=True)


# Actually slideshow's tags can be obtained by visiting http://www.slideshare.net/{{username}}/tag/{{tag.name}}, but:
# 2. doesn't make sense for current crawling method (to obtain all tags for given slideshow, all tag pages for given username have to be visited - cost!)
# 3. low priority, unnecessary : )
@unique_constructor(Session,
    lambda name: name,
    lambda query, name: query.filter(Tag.name == name)
)
class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)


class UserHasTag(Base):
    __tablename__ = 'user_has_tag'
    id = Column(Integer, primary_key=True, autoincrement=True)  # User can have plenty of Tags with the same name. (I know - WTF?!) e.g. http://www.slideshare.net/jiang.wu
    username = Column(String, ForeignKey('user.username'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tag.id'), nullable=False)


class Following(Base):
    __tablename__ = 'following'
    followed_username = Column(String, ForeignKey('user.username'), primary_key=True)
    follower_username = Column(String, ForeignKey('user.username'), primary_key=True)
    followed_user = relationship('User', backref='followed_username', primaryjoin=(User.username == followed_username))
    follower_user = relationship('User', backref='follower_username', primaryjoin=(User.username == follower_username))


class Related(Base):
    __tablename__ = 'related'
    related_ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    relating_ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    related_ss = relationship('Slideshow', backref='relating_ss', primaryjoin=(Slideshow.ssid == related_ssid))
    relating_ss = relationship('Slideshow', backref='related_ss', primaryjoin=(Slideshow.ssid == relating_ssid))


class Like(Base):
    __tablename__ = 'like'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('user.username'), nullable=False)
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), nullable=False)
    user = relationship('User', backref='liked_slideshows', primaryjoin=(User.username == username))
    ss = relationship('Slideshow', backref='liked_by', primaryjoin=(Slideshow.ssid == ssid))


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    username = Column(String, ForeignKey('user.username'), nullable=False)
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), nullable=False)
    user = relationship('User', backref='comments', primaryjoin=(User.username == username))
    ss = relationship('Slideshow', backref='comments', primaryjoin=(Slideshow.ssid == ssid))


Base.metadata.create_all(__engine)

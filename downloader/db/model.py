from datetime import datetime

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()
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
    type_id = Column(Integer, ForeignKey('type.id'))
    username = Column(String, ForeignKey('user.username'))

    downloads_count = Column(Integer, nullable=False)
    views_on_slideshare_count = Column(Integer, nullable=False)
    views_from_embeds_count = Column(Integer, nullable=False)
    embeds_count = Column(Integer, nullable=False)

    # TODO(vucalur): remove when comments & likes implemented
    comments_count = Column(Integer, nullable=False)
    likes_count = Column(Integer, nullable=False)

    categories = relationship('Category', secondary='slideshow_has_category')
    tags = relationship('Tag', secondary='slideshow_has_tag')

    def __setattr__(self, key, value):
        if key in ['created_date', 'updated_date']:
            super(Slideshow, self).__setattr__(key, datetime.strptime(value, DATETIME_FORMAT))
        else:
            super(Slideshow, self).__setattr__(key, value)


class Type(Base):
    __tablename__ = 'type'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slideshows = relationship('Slideshow', backref="type")


class User(Base):
    __tablename__ = 'user'
    username = Column(String, primary_key=True)  # leaving off username (API) as PK
    city = Column(String)
    country_id = Column(Integer, ForeignKey('country.id'))
    organization = Column(String)
    full_name = Column(String)
    description = Column(String)
    joined_date = Column(DateTime)
    slideshows = relationship('Slideshow', backref="user")


class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    slideshows = relationship('Slideshow', secondary="slideshow_has_category")


class SlideshowHasCategory(Base):
    __tablename__ = 'slideshow_has_category'
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), primary_key=True)


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    slideshows = relationship('Slideshow', secondary='slideshow_has_tag')


class SlideshowHasTag(Base):
    __tablename__ = 'slideshow_has_tag'
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)


class Following(Base):
    __tablename__ = 'following'
    followed_username = Column(String, ForeignKey('user.username'), primary_key=True)
    following_username = Column(String, ForeignKey('user.username'), primary_key=True)
    followed_user = relationship('User', backref='following_users', primaryjoin=(User.username == followed_username))
    following_user = relationship('User', backref='follower', primaryjoin=(User.username == following_username))


class Related(Base):
    __tablename__ = 'related'
    related_ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    relating_ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    related_ss = relationship('Slideshow', backref='relating_ss', primaryjoin=(Slideshow.ssid == related_ssid))
    relating_ss = relationship('Slideshow', backref='related_ss', primaryjoin=(Slideshow.ssid == relating_ssid))


class Like(Base):
    __tablename__ = 'like'
    username = Column(String, ForeignKey('user.username'), primary_key=True)
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), primary_key=True)
    user = relationship('User', backref='liked_slideshows', primaryjoin=(User.username == username))
    ss = relationship('Slideshow', backref='liked_by', primaryjoin=(Slideshow.ssid == ssid))


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False)
    text = Column(String)
    username = Column(String, ForeignKey('user.username'), nullable=False)
    ssid = Column(Integer, ForeignKey('slideshow.ssid'), nullable=False)
    user = relationship('User', backref='comments', primaryjoin=(User.username == username))
    ss = relationship('Slideshow', backref='comments', primaryjoin=(Slideshow.ssid == ssid))


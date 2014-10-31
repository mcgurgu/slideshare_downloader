from datetime import datetime

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'


class Slideshow(Base):
    __tablename__ = 'slideshow'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    created_date = Column(DateTime, nullable=False)
    updated_date = Column(DateTime, nullable=False)
    language_code = Column(String, ForeignKey('language.code'))
    format_code = Column(String, ForeignKey('format.code'))
    slideshow_type_code = Column(Integer, ForeignKey('slideshow_type.code'))
    author = Column(String, ForeignKey('user.login'))

    download_count = Column(Integer, nullable=False)
    view_count = Column(Integer, nullable=False)
    embed_count = Column(Integer, nullable=False)
    comment_count = Column(Integer, nullable=False)
    likes_count = Column(Integer, nullable=False)  # favories_count in DOM metadata

    category_name = Column(String, ForeignKey('category.name'))
    tags = relationship('Tag', secondary='slideshow_tag')

    def __setattr__(self, key, value):
        if key in ['created_date', 'updated_date']:
            super(Slideshow, self).__setattr__(key, datetime.strptime(value, DATETIME_FORMAT))
        else:
            super(Slideshow, self).__setattr__(key, value)


class Language(Base):
    __tablename__ = 'language'
    code = Column(String, primary_key=True)
    slideshows = relationship('Slideshow', backref="language")


class Format(Base):
    __tablename__ = 'format'
    code = Column(String, primary_key=True)
    slideshows = relationship('Slideshow', backref="format")


class SlideshowType(Base):
    __tablename__ = 'slideshow_type'
    code = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slideshows = relationship('Slideshow', backref="slideshow_type")


class User(Base):
    __tablename__ = 'user'
    login = Column(String, primary_key=True)
    city = Column(String)
    country = Column(String)
    organization = Column(String)
    full_name = Column(String)
    description = Column(String)
    joined_date = Column(DateTime)
    slideshows = relationship('Slideshow', backref="user")


class Category(Base):
    __tablename__ = 'category'
    name = Column(String, primary_key=True)
    slideshows = relationship('Slideshow', backref="category")


class Tag(Base):
    __tablename__ = 'tag'
    name = Column(String, primary_key=True)
    slideshows = relationship('Slideshow', secondary='slideshow_tag')


class SlideshowTag(Base):
    __tablename__ = 'slideshow_tag'
    slideshow_id = Column(Integer, ForeignKey('slideshow.id'), primary_key=True)
    tag_name = Column(String, ForeignKey('tag.name'), primary_key=True)


class Following(Base):
    __tablename__ = 'following'
    followed_user_login = Column(String, ForeignKey('user.login'), primary_key=True)
    following_user_login = Column(String, ForeignKey('user.login'), primary_key=True)
    followed_user = relationship('User', backref='following_users', primaryjoin=(User.login == followed_user_login))
    following_user = relationship('User', backref='follower', primaryjoin=(User.login == following_user_login))


class RelatedSlideshow(Base):
    __tablename__ = 'related_slideshow'
    related_ssid = Column(Integer, ForeignKey('slideshow.id'), primary_key=True)
    relating_ssid = Column(Integer, ForeignKey('slideshow.id'), primary_key=True)
    related_ss = relationship('Slideshow', backref='relating_ss', primaryjoin=(Slideshow.id == related_ssid))
    relating_ss = relationship('Slideshow', backref='related_ss', primaryjoin=(Slideshow.id == relating_ssid))


class SlideshowLike(Base):
    __tablename__ = 'slideshow_like'
    user_login = Column(String, ForeignKey('user.login'), primary_key=True)
    slideshow_id = Column(Integer, ForeignKey('slideshow.id'), primary_key=True)
    user = relationship('User', backref='liked_slideshows', primaryjoin=(User.login == user_login))
    slideshow = relationship('Slideshow', backref='liked_by', primaryjoin=(Slideshow.id == slideshow_id))


class SlideshowComment(Base):
    __tablename__ = 'slideshow_comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creation_date = Column(DateTime, nullable=False)
    text = Column(String)
    user_login = Column(String, ForeignKey('user.login'), nullable=False)
    slideshow_id = Column(Integer, ForeignKey('slideshow.id'), nullable=False)
    user = relationship('User', backref='comments', primaryjoin=(User.login == user_login))
    slideshow = relationship('Slideshow', backref='comments', primaryjoin=(Slideshow.id == slideshow_id))


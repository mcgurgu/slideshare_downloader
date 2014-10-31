from sqlalchemy import Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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
    favorites_count = Column(Integer, nullable=False)

    category_name = Column(String, ForeignKey('category.name'))
    tags = relationship('Tag', secondary='slideshow_tag')


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


class Follower(Base):
    __tablename__ = 'follower'
    followed_user_login = Column(String, ForeignKey('user.login'), primary_key=True)
    following_user_login = Column(String, ForeignKey('user.login'), primary_key=True)
    followed_user = relationship('User', backref='following_users', primaryjoin=(User.login == followed_user_login))
    following_user = relationship('User', backref='follower', primaryjoin=(User.login == following_user_login))

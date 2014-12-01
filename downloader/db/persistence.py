from sqlalchemy.exc import SQLAlchemyError

from downloader.db.model import User
from downloader.util.logger import log
from downloader.db.model import Session as __session


def save_all_and_commit(data):
    try:
        __session.add_all(data)
        __session.commit()
    except SQLAlchemyError as e:
        log.exception('Caught SQLAlchemyError %s while committing. Rolling back' % (e.message))
        __session.rollback()


def is_user_downloaded(username):
    sole_username = __session \
        .query(User.username) \
        .filter_by(username=username) \
        .scalar()
    return sole_username is not None


def is_follow_network_downloaded(username):
    follow_network_downloaded = __session \
        .query(User.follow_network_downloaded) \
        .filter_by(username=username) \
        .scalar()
    return follow_network_downloaded


def mark_follow_network_as_downloaded(username):
    user = __session.query(User).filter_by(username=username).scalar()
    user.follow_network_downloaded = True
    # TODO(vucalur): check if UPDATE issued when commit() moved elsewhere
    __session.commit()



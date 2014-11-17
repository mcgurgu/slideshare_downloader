import sys
import itertools

from pyquery import PyQuery as pq

from config import Config
from downloader.converter import dict_to_slideshow
from downloader.dictionary_tables import cached_category_ids
from downloader.model import Related, User, Following, SlideshowHasCategory
from downloader.persistence import save_all_and_commit, is_user_processed
from slideshare_api import Pyslideshare


def scrap_remaining_sideshow_info(d, ss):
    ss.embeds_count = int(d('dl.statistics > dd.from-embed').text().replace(',', ''))


def scrap_categories_link(d, ss):
    category_names = [elem.text for elem in d('div.info-generic li.category > a')]
    categories_link = [SlideshowHasCategory(ssid=ss.id, category_id=cat_id)
                       for cat_id in cached_category_ids(category_names)]
    return categories_link


# TODO(vucalur): rename : doesn't scrap Slideshow objects, but RelatedSlideshow objects
# TODO(vucalur): is this even working ?? already had an issue with duplicates in "related" box. TODO: migrate to API
def scrap_related(d, relating_ssid):
    elems = d('ul#relatedList li.j-related-item a')
    related_ids = set(e.attrib['data-ssid'] for e in elems)  # set, since it may return duplicates
    return [Related(
        related_ssid=ssid,
        relating_ssid=relating_ssid) for ssid in related_ids]


def make_user(username, full_name):
    return User(username=username, full_name=full_name)


def make_following(followed_username, following_username):
    return Following(followed_username=followed_username,
        following_username=following_username)


def handle_followers(username, followed_html):
    followed_username = followed_html.find('a').attrib['href'][1:]
    followed_fullname = followed_html.find('a').find('span').text
    following = make_following(username, followed_username)
    if is_user_processed(followed_username):
        return [following]
    else:
        return [following, make_user(followed_username, followed_fullname)]


def handle_following(username, following_html):
    following_username = following_html.find('a').attrib['href'][1:]
    following_fullname = following_html.find('a').find('span').text
    following = make_following(following_username, username)
    if is_user_processed(following_username):
        return [following]
    else:
        return [following, make_user(following_username, following_fullname)]


def calculate_followers_or_following_pages(page):
    pagination_buttons = page('div.pagination li')
    if pagination_buttons:
        return int(pagination_buttons[-2].find('a').text)
    return 1


def scrap_followers(username):
    followers_page = pq(url="http://slideshare.net/%s/followers" % username)
    pages = calculate_followers_or_following_pages(followers_page)
    entities = []
    for p in range(1, pages + 1):
        entities.extend(do_scrap_followers(username, p))
    return entities


def do_scrap_followers(username, page):
    followers_page = pq(url="http://slideshare.net/%s/followers/%d" % (username, page))
    followers_profiles = [x for x in followers_page('ul.userList div.userMeta_profile')]
    relations = [handle_followers(username, followerElement)
                 for followerElement in followers_profiles]
    return list(itertools.chain.from_iterable(relations))


def scrap_following(username):
    following_page = pq(url="http://slideshare.net/%s/following" % username)
    pages = calculate_followers_or_following_pages(following_page)
    entities = []
    for p in range(1, pages + 1):
        entities.extend(do_scrap_following(username, p))
    return entities


def do_scrap_following(username, page):
    following_page = pq(url="http://slideshare.net/%s/following/%d" % (username, page))
    following_profiles = [x for x in following_page('ul.userList div.userMeta_profile')]
    relations = [handle_following(username, followingElement)
                 for followingElement in following_profiles]
    return list(itertools.chain.from_iterable(relations))


def scrap_username_following_and_followers(username):
    save_all_and_commit(scrap_followers(username))
    save_all_and_commit(scrap_following(username))


def process_user(username):
    if not is_user_processed(username):
        if Config['verbose'] == 'True':
            print "\tprocessing username: %s" % username
        save_all_and_commit([User(username=username)])
        scrap_username_following_and_followers(username)
        return [User(username=username)]
    return []


def scrap_and_save_slideshow(ssid):
    print "downloading slideshow with ID: %s" % ssid
    ss_as_dict = api.get_slideshow_by_id(ssid)
    ss = dict_to_slideshow(ss_as_dict)
    d = pq(url=ss.url)
    process_user(ss.username)
    scrap_remaining_sideshow_info(d, ss)
    categories_link = scrap_categories_link(d, ss)
    related = scrap_related(d, ss.id)
    related_ssids = [r.related_ssid for r in related]
    if Config['verbose'] == 'True':
        for r_ssid in related_ssids:
            print "\trelated ID: %s" % r_ssid
    save_all_and_commit(related + [ss] + categories_link)
    return related_ssids


if __name__ == '__main__':
    ssid = sys.argv[1] if len(sys.argv) > 1 else Config['init_ssid']

    api = Pyslideshare()

    scraped = set()
    nonscraped = set()
    nonscraped.add(ssid)

    while len(nonscraped) > 0:
        ssid = nonscraped.pop()
        related_ssids = []
        try:
            related_ssids = scrap_and_save_slideshow(ssid)
        except Exception as e:
            print 'Caught exception %s while processing %s' % (e.message, ssid)
        scraped.add(ssid)
        nonscraped.update(set(related_ssids))
        nonscraped.difference_update(scraped)

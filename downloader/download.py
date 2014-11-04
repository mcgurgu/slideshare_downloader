import sys
import itertools

from pyquery import PyQuery as pq

from config import Config
from downloader.converted import dict_to_slideshow
from downloader.model import RelatedSlideshow, User, Following
from downloader.persistence import save_all_and_commit, get_session
from slideshare_api import Pyslideshare


def scrap_remaining_sideshow_info(d, ss):
    ss.embed_count = int(d('dl.statistics > dd.from-embed').text().replace(',', ''))
    ss.category_name = d('div.info-generic li.category > a').text()


# TODO(vucalur): rename : doesn't scrap Slideshow objects, but RelatedSlideshow objects
# TODO(vucalur): is this even working ?? already had an issue with duplicates in "related" box. TODO: migrate to API
def scrap_related(d, relating_ssid):
    elems = d('ul#relatedList li.j-related-item a')
    related_ids = set(e.attrib['data-ssid'] for e in elems)  # set, since it may return duplicates
    return [RelatedSlideshow(
        related_ssid=ssid,
        relating_ssid=relating_ssid) for ssid in related_ids]

def make_user(username, fullname):
    return User(login=username, full_name=fullname)

def make_following(followed, following):
    return Following(followed_user_login=followed,
                     following_user_login=following)

def handle_followers(username, followedHtml):
    followedUsername = followedHtml.find('a').attrib['href'][1:]
    followedFullname = followedHtml.find('a').find('span').text
    return [make_following(username, followedUsername), 
            make_user(followedUsername, followedFullname)]

def handle_following(username, followingHtml):
    followingUsername = followingHtml.find('a').attrib['href'][1:]
    followingFullname = followingHtml.find('a').find('span').text
    return [make_following(followingUsername, username), 
            make_user(followingUsername, followingFullname)]

def scrap_username_followers(username):
    followersPage = pq(url="http://slideshare.net/%s/followers" % username)
    followersProfiles = [x for x in followersPage('ul.userList div.userMeta_profile')]
    relations = [handle_followers(username, followerElement)
      for followerElement in followersProfiles]
    return list(itertools.chain.from_iterable(relations))

def scrap_username_following(username):
    followingPage = pq(url="http://slideshare.net/%s/following" % username)
    followingProfiles = [x for x in followingPage('ul.userList div.userMeta_profile')]
    relations = [handle_following(username, followingElement)
      for followingElement in followingProfiles]
    return list(itertools.chain.from_iterable(relations))

def scarap_username_following_and_followers(username):
    return scrap_username_followers(username) + scrap_username_following(username)

def scrap_and_save_slideshow(ssid, session):
    print "downloading slideshow with ID: %s" % ssid
    ss_as_dict = api.get_slideshow_by_id(ssid)
    ss = dict_to_slideshow(ss_as_dict)
    d = pq(url=ss.url)
    followingAndFollowers = scarap_username_following_and_followers(ss.author)
    scrap_remaining_sideshow_info(d, ss)
    related = scrap_related(d, ss.id)
    related_ssids = [r.related_ssid for r in related]
    if Config['verbose'] == 'True':
        for r_ssid in related_ssids:
            print "\trelated ID: %s" % r_ssid
    save_all_and_commit(related + [ss] + followingAndFollowers, session)
    return related_ssids


if __name__ == '__main__':
    ssid = sys.argv[1] if len(sys.argv) > 1 else Config['init_ssid']

    api = Pyslideshare()
    session = get_session()

    scraped = set()
    nonscraped = set()
    nonscraped.add(ssid)

    while len(nonscraped) > 0:
        ssid = nonscraped.pop()
        related_ssids = scrap_and_save_slideshow(ssid, session)
        scraped.add(ssid)
        nonscraped.update(set(related_ssids))
        nonscraped.difference_update(scraped)
        nonscraped = []
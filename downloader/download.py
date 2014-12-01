import json
import sys
import itertools
import os
import socket
from urllib import urlopen
from urlparse import urlparse

from pyquery import PyQuery as pq

from downloader.db.model import Related, User, Following, Slideshow, Comment, Like, Tag, Category, Type, Country
from downloader.db.persistence import save_all_and_commit, is_user_downloaded, is_follow_network_downloaded, mark_follow_network_as_downloaded
from downloader.config import config_my as config
from downloader.util.logger import log


scraped_file = 'scraped.txt'
nonscraped_file = 'nonscraped.txt'

timeout = 19
socket.setdefaulttimeout(timeout)


def human_readable_str2int(str_):
    return int(str_.replace(',', '').replace(' ', ''))


def scrap_related(d, relating_ssid):
    elems = d('ul#relatedList li.j-related-item a')
    related_ids = set(e.attrib['data-ssid'] for e in elems)  # set, since page often recommends duplicates
    related_urls = set("http://slideshare.net%s" % e.attrib['href'] for e in elems)
    related_objs = [Related(
        related_ssid=ssid,
        relating_ssid=relating_ssid) for ssid in related_ids]
    return related_objs, related_urls


def download_follow_network(username):
    def download_follow(url_suffix_, new_following):
        def calculate_pages_count(page):
            pagination_buttons = page('div.pagination li')
            if pagination_buttons:
                return int(pagination_buttons[-2].find('a').text)
            return 1

        def handle_profile(profile_element):
            profile_username = profile_element.find('a').attrib['href'][1:]
            if not is_user_downloaded(profile_username):
                obj = new_following(profile_username)
                return [obj, scrap_user(profile_username)]

        def scrap_follow(page_i_):
            page = pq(url="http://slideshare.net/%s/%s/%d" % (username, url_suffix_, page_i_))
            user_profiles = [x for x in page('ul.userList div.userMeta_profile')]
            objs = [handle_profile(profile_element)
                    for profile_element in user_profiles]
            objs = filter(None, objs)
            return list(itertools.chain.from_iterable(objs))

        follow_first_page = pq(url="http://slideshare.net/%s/%s" % (username, url_suffix_))
        pages_count = calculate_pages_count(follow_first_page)
        objs = []
        for page_i in range(1, pages_count + 1):
            log.info("\t\t\tscraping %s, page: %d/%d" % (url_suffix_, page_i, pages_count))
            objs.extend(scrap_follow(page_i))
        return objs

    url_suffix = 'followers'
    followers = download_follow(
        url_suffix,
        lambda follower_username: Following(followed_username=username, follower_username=follower_username))
    save_all_and_commit(followers)
    log.debug("\t\tsaving %s SUCCESS" % url_suffix)

    url_suffix = 'following'
    following = download_follow(
        url_suffix,
        lambda following_username: Following(followed_username=following_username, follower_username=username))
    save_all_and_commit(following)
    log.debug("\t\tsaving %s SUCCESS" % url_suffix)


def scrap_user(username):
    def scrap_tags():
        tags_names = [a_elem.text for a_elem in user_page('#tagsMore span.tagsWrapper span a')]
        tags = [Tag(name=name) for name in tags_names]
        log.info("\t\tfound %d Tag(s)" % len(tags))
        return tags

    user_page = pq(url="http://slideshare.net/%s/" % username)

    full_name = user_page('h1[itemprop="name"]').text()
    city = user_page('span[itemprop="addressLocality"]').text()
    tmp_country_name = user_page('span[itemprop="addressCountry"]').text()
    country = Country(name=tmp_country_name) if tmp_country_name else None
    joined_date = user_page('meta[property="slideshare:joined_on"]')[0].attrib['content']
    url = user_page('a[itemprop="url"]').text()
    about = user_page('span[itemprop="description"]').text()
    works_for = user_page('span[itemprop="worksFor"]').text()

    user = User(
        username=username,
        full_name=full_name,
        country=country,
        city=city,
        joined_date=joined_date,
        url=url,
        about=about,
        works_for=works_for
    )
    user.tags = scrap_tags()
    return user


def process_user(username):
    if not is_user_downloaded(username):
        log.info("\tdownloading User(username=%s)" % username)
        save_all_and_commit([scrap_user(username)])
        log.info("\tdownloading User(username=%s) SUCCESS" % username)
    else:
        log.info("\tdownloading User(username=%s) ALREADY DONE" % username)

    if not is_follow_network_downloaded(username):
        log.info("\tdownloading follow network of User(username=%s)" % username)
        download_follow_network(username)
        mark_follow_network_as_downloaded(username)
        log.info("\tdownloading follow network of User(username=%s) SUCCESS" % username)
    else:
        log.info("\tdownloading follow network of User(username=%s) ALREADY DONE" % username)


def scrap_slideshow(ss_page):
    def scrap_categories():
        # total mess with categories:
        # http://www.slideshare.net/Bufferapp/workspaces-of-buffer-2 - "More in:" - 2 categories
        # but 3from page src: <meta content="Small Business &amp; Entrepreneurship" class="fb_og_meta" property="slideshare:category" name="slideshow_category"> - single category - WTF ?!
        category_names = [elem.text for elem in ss_page('div.categories-container > a')]
        categories = [Category(name=name) for name in category_names]
        return categories

    path_with_ssid = ss_page('meta.twitter_player')[0].attrib['value']
    ss_stats = ss_page('dl.statistics > dd')
    type_name = ss_page('meta[name=og_type]')[0].attrib['content'].split(':')[1]

    ss = Slideshow(
        ssid=int(urlparse(path_with_ssid).path.split('/')[-1]),
        title=ss_page('title')[0].text,
        description=ss_page('meta[name=description]')[0].attrib['content'],
        url=ss_page.base_url,
        created_date=ss_page('meta[name=slideshow_created_at]')[0].attrib['content'],
        updated_date=ss_page('meta[name=slideshow_updated_at]')[0].attrib['content'],
        type=Type(name=type_name),
        username=ss_page('meta[name=slideshow_author]')[0].attrib['content'].split('/')[-1],
        views_on_slideshare_count=human_readable_str2int(ss_stats[1].text),
        views_from_embeds_count=human_readable_str2int(ss_stats[2].text),

        downloads_count=int(ss_page('meta[name=slideshow_download_count]')[0].attrib['content']),
        embeds_count=int(ss_page('meta[name=slideshow_embed_count]')[0].attrib['content'])
    )
    ss.categories = scrap_categories()
    return ss


def get_comments(ssid):
    def json2Comment(comment_json):
        # TODO(vucalur): to consider: schedule downloading commenting User ?
        # TODO(vucalur): many user data are already available in comment_json - performance
        return Comment(
            text=comment_json['body'],
            username=comment_json['login']
        )

    response = urlopen("http://www.slideshare.net/~/slideshow/comments/" + str(ssid))
    comments_json = json.loads(response.read())
    comments = [json2Comment(comment_json) for comment_json in comments_json]
    for comment in comments:
        comment.ssid = ssid
    log.info("\tfound total %d Comment(s)" % len(comments))
    return comments


def get_likes(ssid):
    def json2Like(like_json):
        return Like(
            username=like_json['login']
        )

    likes = []
    offset = 0
    while True:
        response = urlopen("http://www.slideshare.net/~/slideshow/favorites_list/%d?offset=%d" % (ssid, offset))
        new_likes_json = json.loads(response.read())
        if len(new_likes_json) == 0:
            break
        log.info("\t\tdownloaded %d more Like(s)" % len(new_likes_json))
        likes.extend(json2Like(new_like_json) for new_like_json in new_likes_json)
        offset += 20
    for like in likes:
        like.ssid = ssid
    log.info("\tfound total %d Like(s)" % len(likes))
    return likes


def process_slideshow(url):
    log.info("processing Slideshow(url=%s)" % url)
    ss_page = pq(url=url)
    ss = scrap_slideshow(ss_page)
    process_user(ss.username)
    related_objs, related_urls = scrap_related(ss_page, ss.ssid)
    log.info("\tRelated count: %s" % len(related_urls))
    comments = get_comments(ss.ssid)
    likes = get_likes(ss.ssid)
    save_all_and_commit(related_objs + [ss] + comments + likes)
    log.info("processing Slideshow(url=%s) SUCCESS" % url)
    return related_urls


def urls_from_file(filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            return set(list(f))
    return set()


def update_scraped_file(url):
    with open(scraped_file, "a") as f:
        f.write("%s\n" % url.strip())


def update_non_scraped_file(nonscraped):
    with open(nonscraped_file, "w") as f:
        [f.write("%s\n" % n.strip()) for n in nonscraped]


def _main():
    scraped, nonscraped = urls_from_file(scraped_file), urls_from_file(nonscraped_file)
    if not nonscraped:
        url = sys.argv[1] if len(sys.argv) > 1 else config.init_url
        nonscraped.add(url)

    while len(nonscraped) > 0:
        url = nonscraped.pop()
        update_scraped_file(url)
        related_urls = []
        try:
            related_urls = process_slideshow(url)
        except Exception as e:
            log.exception('Caught exception %s while processing Slideshow(url=%s)' % (e.message, url))
        scraped.add(url)
        nonscraped.update(set(related_urls))
        nonscraped.difference_update(scraped)
        update_non_scraped_file(nonscraped)


if __name__ == '__main__':
    _main()

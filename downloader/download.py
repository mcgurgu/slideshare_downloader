import json
import sys
import itertools
from urllib import urlopen
from urlparse import urlparse

from pyquery import PyQuery as pq

from db.model import Related, User, Following, SlideshowHasCategory, Slideshow, Comment, Like
from db.persistence import save_all_and_commit, is_user_processed, get_category_ids
from downloader.config import config_my as config
from downloader.db.persistence import get_type_id, get_country_id
from downloader.util.logger import log


def human_readable_str2int(str_):
    return int(str_.replace(',', '').replace(' ', ''))


def scrap_categories_link(d, ss):
    # total fuck-up with categories:
    # http://www.slideshare.net/Bufferapp/workspaces-of-buffer-2 - "More in:" - 2 categories
    # but 3from page src: <meta content="Small Business &amp; Entrepreneurship" class="fb_og_meta" property="slideshare:category" name="slideshow_category"> - single category - WTF ?!
    category_names = [elem.text for elem in d('div.categories-container > a')]
    categories_link = [SlideshowHasCategory(ssid=ss.ssid, category_id=cat_id)
                       for cat_id in get_category_ids(category_names)]
    log.info("\tcategory IDs: %s" % str([cat_link.category_id for cat_link in categories_link]))
    return categories_link


def scrap_related(d, relating_ssid):
    elems = d('ul#relatedList li.j-related-item a')
    related_ids = set(e.attrib['data-ssid'] for e in elems)  # set, since page often recommends duplicates
    related_urls = set("http://slideshare.net%s" % e.attrib['href'] for e in elems)
    related_objs = [Related(
        related_ssid=ssid,
        relating_ssid=relating_ssid) for ssid in related_ids]
    return related_objs, related_urls


def make_user(username, full_name):
    return User(username=username, full_name=full_name)


def make_following(followed_username, following_username):
    return Following(followed_username=followed_username,
        following_username=following_username)


def calculate_followers_or_following_pages(page):
    pagination_buttons = page('div.pagination li')
    if pagination_buttons:
        return int(pagination_buttons[-2].find('a').text)
    return 1


def scrap_followers(username):
    def handle_followers(username, followed_html):
        followed_username = followed_html.find('a').attrib['href'][1:]
        followed_fullname = followed_html.find('a').find('span').text
        following = make_following(username, followed_username)
        if not is_user_processed(followed_username):
            return [following, make_user(followed_username, followed_fullname)]

    def do_scrap_followers(username, page):
        followers_page = pq(url="http://slideshare.net/%s/followers/%d" % (username, page))
        followers_profiles = [x for x in followers_page('ul.userList div.userMeta_profile')]
        relations = [handle_followers(username, followerElement)
                     for followerElement in followers_profiles]
        relations = filter(None, relations)
        return list(itertools.chain.from_iterable(relations))

    followers_page = pq(url="http://slideshare.net/%s/followers" % username)
    pages = calculate_followers_or_following_pages(followers_page)
    entities = []
    for p in range(1, pages + 1):
        log.info("\t\t\tscraping followers, page: %d/%d" % (p, pages))
        entities.extend(do_scrap_followers(username, p))
    return entities


def scrap_following(username):
    def handle_following(username, following_html):
        following_username = following_html.find('a').attrib['href'][1:]
        following_fullname = following_html.find('a').find('span').text
        following = make_following(following_username, username)
        if not is_user_processed(following_username):
            return [following, make_user(following_username, following_fullname)]

    def do_scrap_following(username, page):
        following_page = pq(url="http://slideshare.net/%s/following/%d" % (username, page))
        following_profiles = [x for x in following_page('ul.userList div.userMeta_profile')]
        relations = [handle_following(username, followingElement)
                     for followingElement in following_profiles]
        relations = filter(None, relations)
        return list(itertools.chain.from_iterable(relations))
        
    following_page = pq(url="http://slideshare.net/%s/following" % username)
    pages = calculate_followers_or_following_pages(following_page)
    entities = []
    for p in range(1, pages + 1):
        log.info("\t\t\tscraping following, page: %d/%d" % (p, pages))
        entities.extend(do_scrap_following(username, p))
    return entities


def scrap_username_following_and_followers(username):
    save_all_and_commit(scrap_followers(username))
    log.debug("\t\tsaving followers SUCCESS")
    save_all_and_commit(scrap_following(username))
    log.debug("\t\tsaving following SUCCESS")


def scrap_user(username):
    user_page = pq(url="http://slideshare.net/%s/" % username)
    # TODO(Szymon): [0].text --> .text(): removes IndexOutOfRange problem if no matches, creates problem if multiple elements match the selector
    full_name = user_page('h1[itemprop="name"]').text()
    city = user_page('span[itemprop="addressLocality"]').text()
    country_name = user_page('span[itemprop="addressCountry"]').text()
    country_id = get_country_id(country_name)
    url = user_page('a[itemprop="url"]').text()
    about = user_page('span[itemprop="description"]').text()
    works_for = user_page('span[itemprop="worksFor"]').text()


    return User(
        username=username,
        full_name=full_name,
        city=city,
        country_id=country_id,
        url=url,
        about=about,
        works_for=works_for
    )


def process_user(username):
    if not is_user_processed(username):
        log.info("\tprocessing User(username=%s)" % username)
        save_all_and_commit([scrap_user(username)])
        scrap_username_following_and_followers(username)
        log.info("\tprocessing User(username=%s) SUCCESS" % username)


def pq_to_slideshow(pq_page):
    path_with_ssid = pq_page('meta.twitter_player')[0].attrib['value']
    ss_stats = pq_page('dl.statistics > dd')
    type_name = pq_page('meta[name=og_type]')[0].attrib['content'].split(':')[1]

    return Slideshow(
        ssid=int(urlparse(path_with_ssid).path.split('/')[-1]),
        title=pq_page('title')[0].text,
        description=pq_page('meta[name=description]')[0].attrib['content'],
        url=pq_page.base_url,
        created_date=pq_page('meta[name=slideshow_created_at]')[0].attrib['content'],
        updated_date=pq_page('meta[name=slideshow_updated_at]')[0].attrib['content'],
        type_id=get_type_id(type_name),
        username=pq_page('meta[name=slideshow_author]')[0].attrib['content'].split('/')[-1],
        views_on_slideshare_count=human_readable_str2int(ss_stats[1].text),
        views_from_embeds_count=human_readable_str2int(ss_stats[2].text),

        downloads_count=int(pq_page('meta[name=slideshow_download_count]')[0].attrib['content']),
        embeds_count=int(pq_page('meta[name=slideshow_embed_count]')[0].attrib['content'])
    )


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
    d = pq(url=url)
    ss = pq_to_slideshow(d)
    process_user(ss.username)
    categories_link = scrap_categories_link(d, ss)
    related_objs, related_urls = scrap_related(d, ss.ssid)
    log.info("\tRelated count: %s" % len(related_urls))
    comments = get_comments(ss.ssid)
    likes = get_likes(ss.ssid)
    save_all_and_commit(related_objs + [ss] + categories_link + comments + likes)
    log.info("saving Slideshow(url=%s) SUCCESS" % url)
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

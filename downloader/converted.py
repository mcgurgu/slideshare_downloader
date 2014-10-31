from downloader.model import Slideshow


def dict_to_slideshow(ss_as_dict):
    return Slideshow(
        id=ss_as_dict['ID'],
        title=ss_as_dict['Title'],
        description=ss_as_dict['Description'],
        url=ss_as_dict['URL'],
        created_date=ss_as_dict['Created'],
        updated_date=ss_as_dict['Updated'],
        language_code=ss_as_dict['Language'],
        format_code=ss_as_dict['Format'],
        slideshow_type_code=int(ss_as_dict['SlideshowType']),
        author=int(ss_as_dict['UserID']),
        download_count=int(ss_as_dict['NumDownloads']),
        view_count=int(ss_as_dict['NumViews']),
        # embed_count - scraping
        comment_count=int(ss_as_dict['NumComments']),
        likes_count=int(ss_as_dict['NumFavorites']),
        # category_name - scraping
        # tags - scraping
    )
from downloader.model import Slideshow


def check_empty(ss_as_dict, property, type=str):
    if 'value' in ss_as_dict[property]:
        return type(ss_as_dict[property].value)
    else:
        return type()


def dict_to_slideshow(ss_as_dict):
    return Slideshow(
        id=check_empty(ss_as_dict, 'ID', int),
        title=check_empty(ss_as_dict, 'Title'),
        description=check_empty(ss_as_dict, 'Description'),
        url=check_empty(ss_as_dict, 'URL'),
        created_date=check_empty(ss_as_dict, 'Created'),
        updated_date=check_empty(ss_as_dict, 'Updated'),
        language_code=check_empty(ss_as_dict, 'Language'),
        format_code=check_empty(ss_as_dict, 'Format'),
        slideshow_type_code=check_empty(ss_as_dict, 'SlideshowType', int),
        author=check_empty(ss_as_dict, 'Username'),
        download_count=check_empty(ss_as_dict, 'NumDownloads', int),
        view_count=check_empty(ss_as_dict, 'NumViews', int),
        # embed_count - scraping
        comment_count=check_empty(ss_as_dict, 'NumComments', int),
        likes_count=check_empty(ss_as_dict, 'NumFavorites', int),
        # category_name - scraping
        # tags - scraping
    )
from downloader.db.dictionary_tables import cached_language_id, cached_format_id
from downloader.db.model import Slideshow


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
        language_id=cached_language_id(
            check_empty(ss_as_dict, 'Language')
        ),
        format_id=cached_format_id(
            check_empty(ss_as_dict, 'Format')
        ),
        type_code=check_empty(ss_as_dict, 'SlideshowType', int),
        username=check_empty(ss_as_dict, 'Username'),
        downloads_count=check_empty(ss_as_dict, 'NumDownloads', int),
        views_count=check_empty(ss_as_dict, 'NumViews', int),
        # embeds_count - scraping
        # categories - scraping
        # tags - scraping
    )
import urllib
import time
from hashlib import sha1
import urllib2

from xml2dict import fromstring
from downloader.config import config_my as config
from downloader.util.logger import log


class Pyslideshare:
    _SLIDESHARE_API_BASE = 'https://www.slideshare.net/api/'
    _API_VERSION = 2
    _service_url_dict = {
        'slideshow_by_user': '%s%d/get_slideshow_by_user' % (_SLIDESHARE_API_BASE, _API_VERSION),
        'get_slideshow': '%s%d/get_slideshow' % (_SLIDESHARE_API_BASE, _API_VERSION),
        'slideshows_by_tag': '%s%d/get_slideshows_by_tag' % (_SLIDESHARE_API_BASE, _API_VERSION),
        'slideshow_by_group': '%s%d/get_slideshow_from_group' % (_SLIDESHARE_API_BASE, _API_VERSION),
        'upload_slideshow': '%s%d/upload_slideshow' % (_SLIDESHARE_API_BASE, _API_VERSION),
        'delete_slideshow': '%s%d/delete_slideshow' % (_SLIDESHARE_API_BASE, _API_VERSION)
    }

    def __init__(self):
        self.api_key = config.api_key
        self.secret_key = config.secret_key
        self.verbose = config.verbose

    def _prepare_url_params(self, **args):
        ts = int(time.time())
        params_dict = {
            'api_key': self.api_key,
            'ts': ts,
            'hash': sha1(self.secret_key + str(ts)).hexdigest()
        }
        # Add method specific parameters to the dict.
        for key, value in args.iteritems():
            # Include only params which has non-null value. Otherwise slideshare is getting screwed up!
            if value and key != 'slideshow_srcfile':
                if isinstance(value, bool):
                    params_dict[key] = '1' if value else '0'
                else:
                    params_dict[key] = str(value)

        return urllib.urlencode(params_dict)

    @staticmethod
    def _check_error(json):
        if json and hasattr(json, 'SlideShareServiceError'):
            log.error('Slideshare returned the following error - %s' % json.SlideShareServiceError.Message)
            return None
        return json

    def _make_call(self, action, **args):
        """
        Handy method which prepares slideshare parameters accepting extra parameters,
        makes service call and returns JSON output
        """
        params = self._prepare_url_params(**args)
        data = urllib2.urlopen(Pyslideshare._service_url_dict[action], params).read()
        as_dict = fromstring(data)
        return self._check_error(as_dict)

    def get_slideshow_by_id(self, ssid):
        slideshow = self._make_call('get_slideshow', slideshow_id=str(ssid), detailed=1)['Slideshow']
        log.debug("\tAPI: get_slideshow call for ssid=%s - SUCCESS" % ssid)
        return slideshow

=========================================
Slideshare downloader
=========================================

Running
=========================================

Running with virtualenv advised

1. install requirements:

  .. code-block:: bash

      $ pip install -r requirements.txt

2. copy ``config.py`` to ``config_my.py`` and provide required values

3. initialize DB:

  .. code-block:: bash

      $ python downloader/db/persistence.py

4. start the download (interrupt with ^C - data are saved after downloading each slideshow):

  .. code-block:: bash

      $ python downloader/download.py

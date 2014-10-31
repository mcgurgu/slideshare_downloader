=========================================
Slideshare downloader
=========================================

Running
=========================================

Running with virtualenv advised

1. install requirements:

  .. code-block:: bash

      $ pip install -r requirements.txt

2. initialize DB:

  .. code-block:: bash

      $ python downloader/persistence.py

3. start the download (interrupt with ^C - data are saved after downloading each slideshow):

  .. code-block:: bash

      $ python downloader/download.py

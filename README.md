# phonograpy
(_heavy miss not using "phonograbby"_)

UMG Recordings, Capitol Records, Universal, Concord Bicycle Assets, CMGI Recorded Music Assets, Sony Music Entertainment and Arista Music have lodged a collective [Complaint](https://www.musicbusinessworldwide.com/files/2023/08/INTERNET-ARCHIVE-BREWSTER-KAHLE-1.pdf) against the Internet Archive. As a user of the net, and archive, I found the situation to be insulting. I won't go into details here, as that's not my job and I'm paid to write programs, not legal journalism. In an effort to support the fight against dying media, I wrote this script in the hopes that it enables some users to more easily grab this collection and share it with the world.


###### _On the off chance anyone from the archive's team sees this, thank you for what you do! Many more people than just I appreciate the effort and your work._
<br/><br/><br/><br/>
## Usage
A Python script for scraping the Internet Archive's [Great78](https://great78.archive.org/) collection of torrent files. Way back when to the times of yesteryear the process of recording audio used to be called "_phonographing_", so of course we've done the usual "smash a -py" on the end of another word to name our script. :)

`78.py [-h] [-s SAVE] [-c CACHE] [-w WORKERS] [-l LOG] [-f LOG_FORMAT]`

Aggregates and downloads the torrent files associated with the George Blood Great78 collection hosted on the Archive. This tool DOES NOT manage, download, or copy the actual data represented by the Great78 collection. We leave this up to the user's discretion.

```
options:
  -h, --help            show this help message and exit
  -s SAVE, --save SAVE  The location to save the torrent files to. Defaults to a relative directory 'torrents/'.
  -c CACHE, --cache CACHE
                        The name for a cache file to generate and/or use in the future. Optional.
  -w WORKERS, --workers WORKERS
                        The number of workers to use when downloading the torrent files. Optional, default: 8
  -l LOG, --log LOG     Set the log level. Optional, default: INFO
  -f LOG_FORMAT, --log-format LOG_FORMAT
                        The format to use when logging. See https://docs.python.org/3/library/logging.html for reference.
```



## Development Stuffs:

This script exposes two classes, an Aggregator and a Downloader. Fairly straightforward.

The Aggregator is responsible for querying the Internet Archive's Scraping API, aggregating all of the results it provides. Since they prefer
the cursor pattern the Aggregator allows you to process a single window of results at a time or all at once. It also allows you to cache these results
(by passing it a path to it's `aggregate` method) so that if you decide to cancel it can pick back up where it left off. This feature is not available with the Downloader.

The Downloader is purely responsible for downloading the `*.torrent` files  associated with the Great 78 collection. There's no filtering or anything fancy, just straight up GET requests. Once we've aggregated them all through our previously described steps we download the torrents to a relative directory `torrents/`, or another that you can specify.


Feel free to fork off this or do your own thing; I don't really care. Please don't expect any updates to this script, or any future development. I made this in an afternoon one weekend because I heard about Sony et al suing the archive. Not cool. 

This software is licensed under the assumption that if you ever meet me IRL you'll buy me a beer for these efforts, which are low. :)

<br/><br/><br/><br/><br/><br/>

###### RIP Aaron Swartz

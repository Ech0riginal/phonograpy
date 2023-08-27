#!/usr/bin/env python3

import logging as log
from argparse import ArgumentParser
from concurrent.futures import Executor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from json import load, loads, dump
from os import mkdir
from os.path import exists
from random import randint
from requests import get as curl
from time import sleep
from typing import List
from tqdm import tqdm

A_GOAT = "georgeblood"


def arguments():
    a = ArgumentParser(
        prog="78.py",
        description="""
        Aggregates and downloads the torrent files associated with the George Blood Great78 collection hosted on the
        Archive. This tool DOES NOT manage, download, or copy the actual data represented by the Great78 collection.
        We leave this up to the user's discretion.
        """
    )
    a.add_argument(
        "-s", "--save",
        help="The location to save the torrent files to. Defaults to a relative directory 'torrents/'.",
        default="torrents"
    )
    a.add_argument(
        "-c", "--cache",
        help="The name for a cache file to generate and/or use in the future. Optional.",
        default=""
    )
    a.add_argument(
        "-w", "--workers",
        help="The number of workers to use when downloading the torrent files. Optional, default: 8",
        default=8,
        type=int
    )
    a.add_argument(
        "-l", "--log",
        help="Set the log level. Optional, default: INFO",
        default="INFO"
    )
    a.add_argument(
        "-f", "--log-format",
        help="The format to use when logging. See https://docs.python.org/3/library/logging.html for reference."
    )
    
    return a.parse_args()


class Record:
    identifier: str
    
    def __init__(self, j):
        self.__dict__ = j


class QueryResults:
    items: List[Record]
    count: int
    cursor: str
    total: int
    
    def __init__(self, j):
        if type(j) is bytes:
            j = loads(j)
        
        if 'cursor' in j:
            self.__dict__ = j
        else:
            self.cursor = None
            self.total = j['total']
            self.count = j['count']
        
        self.items = list(map(lambda r: Record(r), j['items']))
    
    def has_next(self) -> bool:
        return "cursor" in self.__annotations__


class AggMode(int, Enum):
    Full = 0
    """
    The archive's API exposes an interface which uses a cursor pattern, returning a window view of the entire
    collection. 'Full', for lack of a better term, will iterate over all windows until the available cursor has
    completed it's traversal while appending each window's result set to a buffer before returning said buffer.
    """
    Iterative = 1
    """
    Iterative mode is similar to synchronous mode except broken into chunks. Instead of moving through the entire
    collection until returning results, when it receives a single window the result set is stored to the buffer then
    potentially cached and definitely returned.
    """


class Aggregator:
    """ Aggregates all identifiers within the great78 collection. """
    _cursor: str = None
    _cursor_count: int = 0
    _base_url: str = f"https://archive.org/services/search/v1/scrape?q=collection:({A_GOAT})"
    _buffer: List[str] = []
    
    def __init__(
        self,
        mode: AggMode = AggMode.Iterative,
    ):
        self._mode = mode
    
    def cached(self, path: str):
        """ Loads this aggregator from cache. """
        log.debug(f"Rebuilding aggregator off cache.")
        
        if exists(path):
            with open(path, 'r') as f:
                j = load(f)
                self.__dict__ = j
        else:
            log.error(f"Cache file missing")
            
        return self
    
    def aggregate(self, cache: str = None) -> List[str]:
        """
        Aggregates record identifiers across our search query's window(s) and caches the results if necessary.

        See https://archive.org/help/aboutsearch.htm
        """
        if self._mode == AggMode.Full:
            return self.__load_full(cache)
        elif self._mode == AggMode.Iterative:
            return self.__load_iter(cache)
        else:
            return []
    
    def __url(self) -> str:
        """ Builds the URL to GET with the intention of traversing multiple cursors. """
        url = self._base_url
        
        if self._cursor is not None:
            url = f"{self._base_url}&cursor={self._cursor}"
        
        return url
    
    def __load(self) -> List[str]:
        """ Requests the span from Archive and returns all found identifiers. """
        if self._cursor is None:
            return []
        
        response = curl(self.__url())
        content = response.content
        j = loads(content)
        results = QueryResults(j)
        
        self._cursor = results.cursor
        
        return list(map(lambda r: r.identifier, results.items))
    
    def __cache(self, path):
        """ Writes the stored buffer to a file as specified by the `cache` parameter. """
        if path is not None and path != "":
            with open(path, 'w') as f:
                dump(self.__dict__, f)
    
    def __load_iter(self, cache: str = None) -> List[str]:
        if cache is not None:
            cache = f"{cache}_{self._cursor_count}"
            
        results = self.__load()
        self._buffer = self._buffer + results
        self.__cache(cache)
        return results
    
    def __load_full(self, cache: str = None) -> List[str]:
        _ = self.__load_iter()
        while self._cursor is not None:
            _ = self.__load_iter()
        self.__cache(cache)
        return self._buffer


def _torrent_uri(i: str) -> str:
    return f"https://archive.org/download/{i}/{i}_archive.torrent"


@dataclass
class Downloader:
    buffer: List[str]
    """ Contains a list of IDs from the Archive """
    executor: Executor = ProcessPoolExecutor
    """ Sidestep the GIL with a ProcessPoolExecutor but expose it so that others may choose. """
    workers: int = 8
    """ Number of workers to limit the processing pool to."""
    
    @staticmethod
    def __sleep():
        sleep(randint(1000, 10000) / 10000)
    
    @staticmethod
    def _download(id: str, retry: int = 3):
        if exists(Downloader.file_path(id)):
            return
        
        Downloader.__sleep()
        
        uri = _torrent_uri(id)
        response = curl(uri)
        
        try:
            content = response.content
            Downloader._write(id, content)
        except Exception as _:
            if retry > 0:
                log.warning(f"Retrying {id}")
                Downloader._download(uri, retry - 1)
            else:
                log.error(f"Failed to download {uri}")
                return id, None
    
    @staticmethod
    def file_path(id: str):
        return f"torrents/{id}.torrent"
    
    @staticmethod
    def _write(id, content):
        with open(Downloader.file_path(id), 'wb') as f:
            f.write(content)
    
    def download(self):
        l = len(self.buffer)
        log.info(f"Prepping {l} files")
        
        with self.executor(max_workers=self.workers) as pool:
            futs = [pool.submit(Downloader._download, ident, 3) for ident in self.buffer]
            
            log.info(f"Downloading {l} files")
            
            for _ in tqdm(as_completed(futs), total=l):
                pass
        
        log.info(f"Finished downloading great78")


def setup_env(args):
    if not exists(args.save):
        log.warning("Storage directory not present. Will try to create")
        mkdir(args.save)
        log.debug(f"Created {args.save}")


if __name__ == "__main__":
    args = arguments()
    
    setup_env(args)

    log.basicConfig(
        format=args.log_format,
        level=args.log
    )

    identifiers = Aggregator(mode=AggMode.Full)\
        .cached(args.cache)\
        .aggregate(cache=args.cache)
    
    Downloader(identifiers, workers=args.workers)\
        .download()

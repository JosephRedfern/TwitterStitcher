import logging

import tempfile
from typing import List

import subprocess
import tweepy
import requests
import os

# Configure logger
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

logging.basicConfig(
    filename=f"{__location__}/logs.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET_KEY = os.getenv("TWITTER_API_SECRET_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

class TweetStitch:
    def __init__(self, root_tweet_id: int, output_filename: str):
        self._root_tweet_id = root_tweet_id
        self._output_filename = output_filename

        self._tw = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET_KEY,
        )

    def start(self) -> None:
        # We need at least some of these expansions/fields to be able to
        # determine conversation ID and get the media URLs.
        expansions = (
            "attachments.media_keys,author_id,in_reply_to_user_id,referenced_tweets.id"
        )
        media_fields = "variants"
        tweet_fields = (
            "author_id,conversation_id,created_at,in_reply_to_user_id,referenced_tweets"
        )
        user_fields = "name,username"

        logging.info(f"Getting initial tweet to determine conversation ID...")
        first_tweet = self._tw.get_tweets(
            self._root_tweet_id,
            expansions=expansions,
            tweet_fields=tweet_fields,
            media_fields=media_fields,
            user_fields=user_fields,
        )

        username = first_tweet.includes["users"][0].username
        conversation_id = first_tweet.data[0].conversation_id

        medias = []

        # Track pagination token
        next_token = None

        # Loop through pages. Note: we don't do any kind of rate limit checks
        # here. Does Tweepy handle that for us? (probably not...)
        while True:
            logging.info("Getting page of results...")
            response = self._tw.search_recent_tweets(
                query=f"conversation_id:{conversation_id} is:reply from:{username} has:media",
                expansions=expansions,
                tweet_fields=tweet_fields,
                media_fields=media_fields,
                user_fields=user_fields,
                max_results=50,
                next_token=next_token
            )

            medias += response.includes["media"]

            if "next_token" not in response.meta:
                break
            next_token = response.meta["next_token"]

        logging.info("Finished acquiring tweets")

        medias += first_tweet.includes["media"]

        # We need to iterate in reverse order here since the most recent is
        # first, and if we didn't, our re-constructed video would be in reverse
        #order!
        urls = []
        for media in medias[::-1]:
            best_video_url = self.get_best_video(media.variants)
            urls.append(best_video_url['url'])

        # We don't care about keeping the individual chunks, so use a temproary
        # directory.
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self.download_urls(urls, tmpdir)
            self.merge_videos(paths, self._output_filename)

    @staticmethod
    def download_urls(urls: List[str], directory: str) -> None:
        """ Download a list of URLs to the specified directory.

        Assumes mp4, and includes the url index in the filename (e.g. 1.mp4)

        Returns an ordered list of paths.
        """

        logging.info(f"Downloading {len(urls)} to {directory}")
        paths = []

        for n, url in enumerate(urls):
            logging.info(f"Downloading video {n+1}/{len(urls)} ({url})")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                path = f"{directory}/{n}.mp4"
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                paths.append(path)
        return paths

    @staticmethod
    def merge_videos(paths: List[str], output: str) -> None:
        """ Concatenate the specified list of videos using `ffmpeg`.

        To do this, we need to generate a list of files to pass to the concat
        demuxer: https://trac.ffmpeg.org/wiki/Concatenate. We then pass this
        file to `ffmpeg`.

        A bit gross, no bindings used here, just subprocess... but it works?
        """


        # We need to prevent deletion as we can't keep the write handle open
        # and also pass to ffmpeg. So prevent automatic deletion, pass the
        # filename to ffmpeg, then delete the temporary file in the `finally`
        # block
        with tempfile.NamedTemporaryFile('w', delete=False) as command_file:
            try:
                for path in paths:
                    command = f"file '{path}'\n"
                    command_file.write(command)
                command_file.close()
                subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", command_file.name, "-c", "copy", output])
            finally:
                os.unlink(command_file.name)

    def get_best_video(self, variants: list) -> dict:
        """ Identify variant with the highest bit-rate, and return a download
        URL.

        Note: at least one of these variants always seems to be a playlist
        URL rather than an actual video download URL -- that URL is missing a
        bitrate field, so we filter before sorting.
        """

        video_urls = [v for v in variants if "bit_rate" in v]
        sorted_variants = sorted(video_urls, key=lambda x: x["bit_rate"])

        return sorted_variants[-1]

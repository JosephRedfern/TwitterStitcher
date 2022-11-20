TweetStitch
===========

Extracts videos from Twitter threads and concatenate using `ffmpeg`.

This tool works by:
* Requesting the specified tweet from Twitter, extracting the conversation ID.
* Retrieving other media-containing tweets, from the original author, within that conversation, in chronological order.
* Extracting the highest quality media URL from those tweets, downloading to a temporary directory.
* Calling off to `ffmpeg` to concatenate the downloaded videos together, using the `concat` ffmpeg demuxer.

It seems to work OK, but things might start to go horribly wrong if video dimensions don't match up 

# Usage
```
python -m tweetstitch TWEET_URL OUTPUT_FILENAME
```

# Installation 
Python Dependencies are managed using [Poetry](https://python-poetry.org)  -- having installed poetry, run:

```
poetry install
```

from the root of this repository.

This tool also depends on ffmpeg -- it'll need to be on your system PATH

# Configuration
This tool makes use of the Twitter API. You'll need to register for the Twitter API and set variables for:

* `TWITTER_BEARER_TOKEN`
* `TWITTER_API_KEY`
* `TWITTER_API_SECRET_KEY`

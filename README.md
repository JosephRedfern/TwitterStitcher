TweetStitch
===========

Extracts videos from Twitter threads and concatenate using `ffmpeg`.

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

import typer
from tweetstitch import stitch


def main(tweet_url: str, output: str) -> None:
    # Extract Tweet ID from Tweet URL
    tweet_id = tweet_url.split('/')[-1].split('?')[0]

    stitcher = stitch.TweetStitch(
        root_tweet_id=tweet_id,
        output_filename=output
    )

    stitcher.start()


if __name__ == "__main__":
    typer.run(main)

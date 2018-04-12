"""Module for adding tweets to Mongo DB."""
import bz2
import json
from pymongo import MongoClient
import itertools as it
import os
from pymongo.errors import DuplicateKeyError


class AddHistoricalTweets:
    """Adds a months worth of tweets to the DB based on word search filters."""

    def __init__(self, month, year, mdb="mongodb://localhost/twitterdb",
                 filter_=dict()):
        """
        Initialize.

        :param month: int
            Integer representing month.
        :param year: int
            Integer representing year.
        :param mdb: string
            String indicating the mongodb connection.
        :param filter_: dict
            Dictionary of the terms that need to be filtered for.
        """
        home = os.path.expanduser("~")
        self.module = (
            'archiveteam-twitter-stream-'
            '{y:04d}-{m:02d}'.format(y=year, m=month))
        self.down_dir = home + '/Downloads/' + self.module
        self.year = year
        self.month = month
        self.exdir = self.down_dir + "/{y:04d}/{m:02d}".format(y=year, m=month)
        self.MONGO_HOST = mdb
        self.client = MongoClient(self.MONGO_HOST)
        self.db = self.client.twitterdb
        self.filter = filter_
        self.base = (
            home + "/Downloads/" +
            "archiveteam-twitter-stream-{y:04d}-{m:02d}/{y:04d}/" +
            "{m:02d}/{d:02d}/{h:02d}/{n:02d}.json.bz2")

    def load_archived_tweets(self):
        """Load archived tweets to DB."""
        vals = [range(32), range(24), range(60)]
        for d, h, mi in it.product(*vals):
            f_ = self.base.format(y=self.year, m=self.month, d=d, h=h, n=mi)
            if not os.path.isfile(f_):
                continue
            print("Entering File: " + f_)
            # open the bz2 file
            input_file = bz2.BZ2File(f_, 'r')
            # have a place to store the tweets
            tweets = []
            # runline by line and grab the tweets
            try:
                for line in input_file.readlines():
                    tweets.append(json.loads(line))
            except ValueError:
                continue
            for t in tweets:
                self.load_tweet(t)

    def load_tweet(self, t, verbose=False):
        """Load a single tweet to the DB."""
        if "delete" in t.keys():
            if verbose:
                print("Tweet does not have any content.")
            return
        if t["user"]["lang"] != "en":
            if verbose:
                print("Tweet not marked as english.")
            return
        tz = t["user"]["time_zone"]
        if tz is None or "US" not in tz:
            if verbose:
                print("Tweet does not match US timezone")
            return
        for col in self.filter.keys():
            for term in self.filter[col].keys():
                kwords = self.filter[col][term]
                if "retweeted_status" in t.keys():
                    ttext = t["retweeted_status"]["text"].lower()
                else:
                    ttext = t["text"].lower()
                if any([k.lower() in ttext for k in kwords]):
                    if verbose:
                        print("adding New tweet for {}!!!!".format(term))
                    t["collection"] = col
                    t["term"] = term
                    try:
                        self.db.twitter_search.insert_one(t)
                    except DuplicateKeyError:
                        if verbose:
                            print("Tweet already in the DB.")
                        return
                else:
                    if verbose:
                        print("Tweet does not match any filter.")
                    return


if __name__ == "__main__":
    from WordSearchList import word_search_list
    from TwitterDL import TwitterDL
    # lets input the first ten months of 2017 in reverse order
    for month in range(10, 0, -1):
        year = 2017
        tdl = TwitterDL(month, year)
        tdl.download_torrent()
        tdl.extract_data()
        tweet2db = AddHistoricalTweets(month, year, word_search_list)
        tweet2db.load_tweets()
        tdl.remove_folder()

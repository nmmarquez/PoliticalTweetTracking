"""Code to pull and upload user history."""
from tweepy import OAuthHandler, API, TweepError
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import json
import argparse
import time
import os


class AddHistoricalTweets:
    """Adds a months worth of tweets to the DB based on word search filters."""

    def __init__(
        self,
        userID,
        twitCred=None,
        consumerKey=None,
        consumerSecret=None,
        accessToken=None,
        accessSecret=None,
        mdb="mongodb://localhost/twitterdb"
    ):
        """
        Initialize.

        :param userID: int
            Integer representing the users ID.
        :param mdb: string
            String indicating the mongodb connection.
        """
        self.MONGO_HOST = mdb
        self.client = MongoClient(self.MONGO_HOST)
        self.db = self.client.twitterdb
        self.userID = userID
        valid = (
            twitCred |
            (consumerKey & consumerSecret & accessToken & accessSecret)
        )
        assert valid, "Invalid twitter API credentials"
        if twitCred:
            with open(twitCred) as json_data:
                d = json.load(json_data)
            consumerKey = d["consumerKey"]
            consumerSecret = d["consumerSecret"]
            accessToken = d["accessToken"]
            accessSecret = d["accessSecret"]
        auth = OAuthHandler(consumerKey, consumerSecret)
        auth.set_access_token(accessToken, accessSecret)
        self.api = API(auth)

    def pullUserHistory(self, verbose=False, return_calls=False):
        """
        Pull a users complete history up to the last 32000 tweets.

        :param userID: int, The users unique identification.
        :param verbose: bool, Print verbose text.
        :param return_calls: bool, return the number of calls made to API.
        :return: list, list of tweets by user.
        """
        uHistLast = self.api.user_timeline(self.userID, count=200)
        uHistTotal = uHistLast.copy()
        total = 200
        calls = 1
        while total != 3200 and len(uHistLast) != 0:
            max_id = uHistLast[-1]._json["id"]-1
            uHistLast = self.api.user_timeline(
                self.userID,
                count=200,
                max_id=max_id)
            uHistTotal += uHistLast
            total += 200
            calls += 1
        if verbose:
            print(str(calls) + " calls to API made.")
        if return_calls:
            return uHistTotal, calls
        return uHistTotal

    def uploadUserHistory(self, return_calls=False):
        """
        Upload a users lastest tweets to a mongodb.

        :param return_calls: bool, return the number of calls made to API.
        :return: int, optional, number of calls made to API.
        """
        uHist, calls = self.pullUserHistory(return_calls=True)
        for x in uHist:
            t = x._json
            t["collection"] = "user"
            t["term"] = t["id_str"]
            try:
                self.db.twitter_search.insert_one(t)
            except DuplicateKeyError:
                print("Tweet already in the DB.")
        if return_calls:
            return calls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Command line utility to upload Users Twitter History to"
            "a running instance of mongodb."
        ))
    parser.add_argument('-i', '--idlist', help='User ID list', type=str)
    args = parser.parse_args()
    userIDs = [int(item) for item in args.idlist.split(',')]
    totalCalls = 0
    for i, u in enumerate(userIDs):
        time.sleep(10)
        try:
            tpath = os.path.expanduser("~/.twitcred.txt")
            uMod = AddHistoricalTweets(u, twitCred=tpath)
            totalCalls += uMod.uploadUserHistory(True)
        except TweepError:
            print("Error at user: " + str(i))
            continue

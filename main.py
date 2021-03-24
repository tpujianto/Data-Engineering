import sqlalchemy
import pandas as pd
from sqlalchemy.orm import sessionmaker
import requests
import json
from datetime import datetime
import datetime
import sqlite3

DATABASE_LOCATION = "sqlite://my_played_tracks.sqlite"
USER_ID = "theopujianto"
TOKEN = "BQAdBtgFc3LKUuI5dLj24wkO62aLKV8BGxn9zYRlnGz1mae2wXsZar_C3BM5XKjLdaQ-ItDUbH8o59sYInVk5nSrCD17TvnNKyXvyT4ajjmruifljubD8gEabbgtJgw7kAFBg5L2KvgDifx8wuO53B4"

def check_if_data_valid(df: pd.DataFrame) -> bool:
    # check if the data is valid
    if df.empty:
        print("No songs streamed. Finish execution.")
        return False
    
    # primary key check - in this case, it's the time when you listen the songs, you cannot listen to 2 songs with 1 account at any given time
    if pd.Series(df['played_at']).is_unique:
        pass
    else:
        raise Exception("Primary Key check is violated.")

    # check for nulls
    if df.isnull().values.any():
        raise Exception("Null values found.")

    # check that all timestamps are of yesterday's date
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    timestamps = df['timestamps'].tolist()
    for timestamp in timestamps:
        if datetime.datetime.strptime(timestamp, '%Y-%m-%d') != yesterday:
            raise Exception("At least one of the returned songs does not have a yesterday's timestamp")

    return True


if __name__ == "__main__":
    

    # start with passing required header
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer {token}".format(token=TOKEN)
    }

    # time needs to be converted to Unix timestamp in miliseconds
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_unix_timestamp = int(yesterday.timestamp()) * 1000

    # download all songs you've listened to "after yesterday", which means in the last 24 hours
    # Download all songs you've listened to "after yesterday", which means in the last 24 hours
    r = requests.get("https://api.spotify.com/v1/me/player/recently-played?after={time}".format(
        time=yesterday_unix_timestamp), headers=headers)

    data = r.json()

    song_names = []
    artist_names = []
    played_at_list = []
    timestamps = []
    
    # for loop at the data and take what we need
    for song in data["items"]:
        song_names.append(song["track"]["name"])
        artist_names.append(song["track"]["album"]["artists"][0]["name"])
        played_at_list.append(song["played_at"])
        timestamps.append(song["played_at"][0:10])

    # prepare a dictionary in order to turn it into a pandas dataframe below
    song_dict = {
        "song_name": song_names,
        "artist_name": artist_names,
        "played_at": played_at_list,
        "timestamp": timestamps
    }

    song_df = pd.DataFrame(song_dict, columns=[
                           "song_name", "artist_name", "played_at", "timestamp"])

    # do validation
    if check_if_data_valid(song_df):
        print("Data is valid. Proceed.")


    # load
    engine = sqlalchemy.create_engine(DATABASE_LOCATION)
    conn = sqlite3.connect("my_played_tracks.sqlite")
    cursor = conn.cursor()

    sql_query = """
    CREATE TABLE IF NOT EXISTS my_played_tracks(
        song_name VARCHAR(200),
        artist_name VARCHAR(200),
        played_at VARCHAR(200),
        timestamp VARCHAR(200),
        CONSTRAINT primary_key_constraint PRIMARY KEY (played_at)
    )
    """
    cursor.execute(sql_query)
    print("Opened database successfully")

    try:
        song_df.to_sql("my_played_tracks", engine,
                       index=False, if_exists='append')
    except:
        print("Data already exists in the database")

    conn.close()
    print("Close database successfully")

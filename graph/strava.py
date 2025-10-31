import logging
import pickle
from pathlib import Path

import gpxpy
import numpy as np
import pandas as pd

from garmin_fit_sdk import Decoder, Stream

INT_DEGREES = 2**32 / 360


def create_routes(instance_name: str, logger: str = None):
    """Create a dataframe for each Strava activity and save list of all dataframes to a pickle file.

    Args:
        instance_name (str): The name of the instance to create routes for.
        logger (str, optional): The name of the logger to use. Defaults to None.
    """
    logger = logging.getLogger(logger)
    logger.info(f"Processing route data for {instance_name}...")

    activities_df = pd.read_csv(f"strava_data_{instance_name.split('-')[0]}/activities.csv", index_col=0)

    # limit to only runs and walks
    activities_df = activities_df[activities_df["Activity Type"].isin(["Run", "Walk"])]

    routes = []
    for _, row in activities_df.iterrows():
        filename = f"strava_data_{instance_name.split('-')[0]}/" + row["Filename"]

        # trim any compressed file extensions
        if filename.endswith(".gz"):
            filename = filename[:-3]

        # skip if the file doesn't exist
        if not Path(filename).exists():
            continue

        # get a dataframe of all lat/long points
        if filename.endswith(".fit"):
            df = get_fit_df(filename)
        elif filename.endswith(".gpx"):
            df = get_gpx_df(filename)
        else:
            continue

        # skip if no data was found
        if df is None:
            continue

        # correct lat/long values if stored as ints
        if df["position_lat"].max() > 90:
            df = df / INT_DEGREES

        routes.append(df.dropna())

    # save routes to file
    with open(f"routes_{instance_name}.pkl", "wb") as file:
        pickle.dump(routes, file, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info(f"Processed {len(routes)} routes for {instance_name}.")


def get_fit_df(filename: str) -> pd.DataFrame | None:
    """Read a .fit file and return a dataframe of its contents, or None if file doesn't have expected format.

    Args:
        filename (str): The filenmae of the .fit file to read.

    Returns:
        pd.DataFrame | None: A dataframe with columns postion_lat and position_long, indexed by timestamp.
    """
    # read file
    decoder = Decoder(Stream.from_file(filename))
    messages, _ = decoder.read(convert_datetimes_to_dates=True)

    if not messages or "record_mesgs" not in messages:
        return

    record = messages["record_mesgs"]

    # if no position data, return
    if "position_lat" not in record[0]:
        return

    # create dataframe
    df = pd.DataFrame(record)
    df = df.set_index("timestamp")[["position_lat", "position_long"]]

    return df


def get_gpx_df(filename: str) -> pd.DataFrame:
    """Read a .gpx file and retuern a dataframe of its contents.

    Args:
        filename (str): The filename of the .gpx file to read.

    Returns:
        pd.DataFrame: A dataframe with columns position_lat and position_long, indexed by timestamp.
    """
    # read file
    with open(filename, encoding="utf-8") as file:
        gpx = gpxpy.parse(file)

    # extract all gps points
    points = []
    for segment in gpx.tracks[0].segments:
        for point in segment.points:
            points.append(
                {
                    "timestamp": point.time,
                    "position_lat": point.latitude,
                    "position_long": point.longitude,
                }
            )

    # create dataframe
    df = pd.DataFrame.from_records(points)
    df = df.set_index("timestamp")

    return df

import time
from datetime import datetime, timedelta, timezone
from .bitstream_utils import SimpleBitStream


def get_ingame_time():
    """
    Calculate ingame time based on the following formula:
    1. Take current unix time in seconds
    2. Subtract seconds in 1998.8.21 10:00:00
    3. Multiply the resulting amount of seconds by 12
    4. Return the result as if that many seconds passed from 0001.1.1 00:00:00

    Returns:
        datetime: The calculated ingame time
    """
    current_unix_time = time.time()

    reference_date = datetime(1998, 8, 21, 10, 0, 0, tzinfo=timezone.utc)
    reference_unix_time = reference_date.timestamp()
    time_difference = current_unix_time - reference_unix_time
    accelerated_seconds = time_difference * 12

    # Start from year 1 and add the accelerated seconds using timedelta
    base_date = datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    ingame_time = base_date + timedelta(seconds=accelerated_seconds)

    return ingame_time


def encode_ingame_time() -> bytes:
    ingame_time = get_ingame_time()
    seconds = int(ingame_time.second / 12 + 1)
    minutes = ingame_time.minute
    hours = ingame_time.hour
    days = ingame_time.day
    months = ingame_time.month
    years = ingame_time.year

    stream = SimpleBitStream()
    stream.write_int(seconds, 4)
    stream.write_int(minutes, 6)
    stream.write_int(hours, 5)
    stream.write_int(days, 5)
    stream.write_int(months, 4)
    stream.write_int(years, 10)
    stream.write_int(0b1101, 4)

    return stream.to_bytes()

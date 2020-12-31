import json
import re
import time
import os
from operator import xor
from functools import reduce
from binascii import hexlify

import serial
from RPi import GPIO as GPIO
from pydantic import BaseModel, ValidationError
from typing import Tuple


# Define outside of main loop to save time
class Wind(BaseModel):
    t: int  # time
    h: int  # heading
    s: float  # speed
    u: str  # units
    k: str  # status


# Precompile regex used in main loop
bpattern = re.compile(b"\x02(?P<payload>.*)\x03(?P<checksum>.*)\x0d\x0a")
pattern = re.compile("Q,(?P<heading>.*),(?P<speed>.*),(?P<units>.*),(?P<status>.*),")


def set_pin_states():
    """
    Sets pins on Rpi to support RS485 daughterboard
    :return: None. Changes state of Rpi pins
    """
    EN_485 = 4
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(EN_485, GPIO.OUT)
    GPIO.output(EN_485, GPIO.LOW)
    return None


def stream_wind() -> Tuple[str, str]:
    """
    Generate wind data and error data from anemometer
    :yield: tuple of [wind, error]
    :example: This is a generator, so typical use might be
    for wind, error in stream_wind():
          print(f"Wind json: {wind}, if there was an error it was: {error})
    """
    with serial.Serial("/dev/serial0", 9600, timeout=0.5, write_timeout=0.5) as ser:
        while True:
            ser.write(b"?Q")
            s = ser.readall()
            t = (
                time.clock_gettime_ns(time.CLOCK_REALTIME) // 1_000_000
            )  # Epoch in milliseconds
            yield from wind_data_from_bytes(s, t)


def wind_data_from_bytes(s: bytes, t: int) -> Tuple[str, str]:
    """
    Extract wind data as json from raw anemometer bytes

    :param s: byte string from anemometer
    :param t: epoch in milliseconds
    :return: tuple of a json string and an error string, one of which will be an empty string
    """
    match = bpattern.match(s)
    if (not match) or (
        not all(key in match.groupdict() for key in ("payload", "checksum"))
    ):
        err = f"Failed payload match. Got bytes: {hexlify(s, '-')}"
        return "", err
    if int(match["checksum"].decode("utf8"), base=16) != reduce(xor, match["payload"]):
        return "", f"Checksum bad. Got bytes: {hexlify(s, '-')}"
    payload = pattern.match(match["payload"].decode("utf8"))
    try:
        answer = Wind(
            t=t,
            h=payload["heading"] or 0,
            s=payload["speed"],
            u=payload["units"],
            k=payload["status"],
        )
        return json.dumps(answer.dict()), ""
    except ValidationError as e:
        err = f"{payload.groupdict()} -> {e}"
        return "", err


if __name__ == "__main__":
    set_pin_states()
    for wind, error in stream_wind():
        if wind:
            print(wind, file=os.stdout)
        else:
            print(error, file=os.stderr)

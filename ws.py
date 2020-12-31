import json
import re
import time

import serial
from RPi import GPIO as GPIO
from pydantic import BaseModel, ValidationError


class Wind(BaseModel):
    t: int  # time
    h: int  # heading
    s: float  # speed
    u: str  # units
    k: str  # status


def main():
    setup_pins()
    reading = generate_raw_anemometer_bytes()
    get_payload = validate_extract_payload()
    next(get_payload)
    while True:
        s, t = next(reading)
        payload = get_payload.send(s)
        try:
            answer = Wind(
                t=t,
                h=payload["heading"] or 0,
                s=payload["speed"],
                u=payload["units"],
                k=payload["status"],
            )
        except ValidationError as e:
            print(e)  # TODO this should be logged
        print(json.dumps(answer.dict()))
        # next(get_payload)


def validate_extract_payload():
    bpattern = re.compile(b"\x02(?P<payload>.*)\x03(?P<checksum>.*)\x0d\x0a")
    pattern = re.compile("Q,(?P<heading>.*),(?P<speed>.*),(?P<units>.*),(?P<status>.*),")
    while True:
        s = (yield payload)
        print(s)
        match = bpattern.match(s)
        chk_sum = 0
        for c in match["payload"]:
            chk_sum ^= c
        if int(match["checksum"].decode("utf8"), base=16) != chk_sum:
            print(
                f"Checksum bad. Got bytes: {' '.join(format(c, '02x') for c in s)}"
            )  # TODO: Make this a log and not a print
        payload = pattern.match(match["payload"].decode("utf8"))


def setup_pins():
    EN_485 = 4
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(EN_485, GPIO.OUT)
    GPIO.output(EN_485, GPIO.LOW)


def generate_raw_anemometer_bytes():
    with serial.Serial("/dev/serial0", 9600, timeout=0.5) as ser:
        while True:
            ser.write(b"?Q")
            ser.readall()
            t = (
                    time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000000
            )  # Epoch in
            yield s, t


if __name__ == '__main__':
    main()
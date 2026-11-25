import binascii
import struct
import time
import random

from dataclasses import dataclass
from enum import IntEnum

MAGIC = 0xAA55
VERSION = 2

BODY =struct.Struct(">HBBIQHBBIIH")

PACKET_SIZE = BODY.size + 2

BID = 0
ASK = 1

MAX_QUANTITY = 1000

class Event(IntEnum):
    ADD = 1
    MODIFY = 2
    CANCEL =3
    EXECUTE= 4

@dataclass (frozen=True)
class Update:
    sequence: int
    timestamp_ns: int
    instrument: int
    side: int
    event: Event
    price: int
    quantity: int

    def encode(self) -> bytes:

        body = BODY.pack(
            MAGIC,
            VERSION,
            int(self.event),
            self.sequence,
            self.timestamp_ns,
            self.instrument,
            self.side,
            0,
            self.price,
            self.quantity,
            0
        )

        checksum = binascii.crc_hqx(body, 0xFFFF)
        return body + struct.pack(">H", checksum)

class book:
    def __init__(self, low: int, depth: int):

        self.low = low
        self.depth = depth
        self.side = [{}, {}]

    def apply(self, update = Update):
        assert self.low <= update.price < self.low + self.depth

        levels = self.sides[update.side]
        if update.quantity:
            levels[update.price] = update.quantity
        else:
            levels.pop(update.price, None)

        bids, asks = self.sides
        assert not (
            bids
            and asks
            and max(bids) >= min(asks)
        )

    def metrics(self) -> dict:

        bids, asks = self.sides
        best_bid = max(bids, default = 0)
        best_ask = min(asks, default = 0)

        spread = (
            best_ask - best_bid
            if best_bid and best_ask
            else None
        )
        bid_volume = sum(bids.values())
        ask_volume = sum(asks.values())
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bid_quantity": bids.get(best_bid, 0),
            "ask_quantity": asks.get(best_ask, 0),
            "spread": spread,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "imbalance_numerator": bid_volume - ask_volume,
            "imbalance_denominator": bid_volume + ask_volume
        }

class Generator:

    def __init__(self, args):
         
         self.a = args
         self.rng = random



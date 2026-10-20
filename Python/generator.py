import random
import struct
import time
from dataclasses import dataclass

LEVELS = 5
MID_PRICE_CENTS = 10_000 #this is stored as £100.00 as integer cents
HALD_SPREAD_CENTS = 2
TICK_CENTS = 1
RANDOM_UPDATES =30
DELAY_SECONDS = 0.0 # increase to slow down the feed

BID = 0
ASK = 1
MAGIC = 0xAA55

PACKET_FORMAT = ">HIBBIH"
# Fixed to 14 byte packet
# magic(2), sequence(4), side(1), level(1), price(4), qty(2), '>' means big-endian
# in future a timestamp, message type, and checksum will need to be added later

@dataclass
class MarketUpdates:
  sequence: int
  side: int
  level: int
  price_cents: int
  quantity: int

def price_for(side:int, level:int) -> int:
  """
    Calculate the price at a given order book level
  """
  
  offset = HALF_SPREAD_CENTS + level + TICK_CENTS

  if side == BID:
    return MID_PRICE_CENTS - offset
  else:
    return MID_PRICE_CENTS + offset
  # in the future allow MID_PRICE_CENTS to change over time 
, when the price moves, update the affected book levels

def encode_packet(update: MarketUpdate) -> bytes:
  """
    Convert an update into bytes for the FPGA
  """
  
  return struct.pack(
    PACKET_FORMAT,
    MAGIC,
    update.sequence,
    update.side,
    update.level,
    update.price_cents,
    update.quantity,
  )

def generate_update(count=RANDOM_UPDATES, seed=42):
  rng = random.Random(seed) # done this to make replicable results
  sequence = 0
  for side in (BID, ASK):
    for level in range(LEVELS):
      yield MarketUpdates(
        sequence,
        side,
        level,
        price_for(side, level),
        rng.randint(10,1000),
      )
      sequence += 1
      
  for _ in range(count):
    side = rng.choice((BID, ASK))
    level = rng.randrange(LEVELS)
    quantity = (
      0 if rng.random() < 0.1 else rng.randint(1, 1000) # want to clear a level occasionally, done this via setting quantity to 0
    )
    update = MarketUpdate(
      sequence,
      side,
      level,
      price_for(side, level),
      quantity,
    )
    yeild update
    sequence += 1
# in the future add: dynamically changing prices, trades and cancellations, simulate bursts in the market, and multiple stocks 
# this is the section which will change the most after a GA goes through actual market data

def main():
  with open("market_data.bin", "wb") as output:
    for update in generate_updates():
      packet = encode_packet(update)
      output.write(packet)
      # for this version this will save the raw bytes in future need to add a serial writefor sending to FPGA

      side_name = "BID" if update.side == BID else "ASK"
      print(f"#{update.sequence:03d} "
            f"{side_name} "
            f"L{update.level} "
            f"${update.price_cents / 100:.2f} "
            f"qty={update.quntity} " 
            f"-> {packet.hex(' ')}"
           )
      
    time.sleep(DELAY_SECONDS)
      
if __name__ == "__main__":
  main()

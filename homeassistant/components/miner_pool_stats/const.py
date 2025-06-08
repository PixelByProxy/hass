"""Constants for the Miner Pool Stats integration."""

from enum import StrEnum

DOMAIN = "miner_pool_stats"

POOL_SOURCE_PUBLIC_POOL_KEY = "public_pool"
POOL_SOURCE_PUBLIC_POOL_NAME = "Public Pool"
POOL_SOURCE_F2_POOL_KEY = "f2_pool"
POOL_SOURCE_F2_POOL_NAME = "f2pool"
POOL_SOURCE_SOLO_POOL_KEY = "solo_pool"
POOL_SOURCE_SOLO_POOL_NAME = "SoloPool.org"

WALLET_ADDRESS = "Wallet Address"
WORKER = "Worker"

KEY_WORKER_COUNT = "worker_count"
KEY_BEST_DIFFICULTY = "best_difficulty"
KEY_HASH_RATE = "hash_rate"
KEY_START_TIME = "start_time"
KEY_LAST_SEEN = "last_seen"

UNIT_WORKER_COUNT = "workers"
UNIT_HASH_RATE = "TH/s"
UNIT_DIFFICULTY = "difficulty"


class CryptoCoinsF2Pool(StrEnum):
    """List of supported crypto coins by f2pool."""

    BTC = "bitcoin"
    BCH = "bitcoin-cash"
    LTC = "litecoin"
    ALEO = "aleo"
    KAS = "kaspa"


class CryptoCoinsSoloPool(StrEnum):
    """List of supported crypto coins by Solo Pool."""

    BTC = "btc"
    BCH = "bch"
    KAS = "kas"

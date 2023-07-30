"""Top-level package for ATC Clearance Delivery Simulator."""

__author__ = """Philippe Dellaert"""
__email__ = "philippe@dellaert.org"
__version__ = "0.1.0"

__all__ = [
    "AdsConfig",
    "get_ifr_flight_plans",
    "fetch_aircraft",
    "fetch_operator",
    "generate_vfr_flight_plans",
    "get_rules_info",
]

from atc_del_simulator.ads_config import AdsConfig
from atc_del_simulator.atc_del_simulator import (
    get_ifr_flight_plans,
    fetch_aircraft,
    fetch_operator,
    generate_vfr_flight_plans,
    get_rules_info,
)

"""Main module."""
import random
import math
from datetime import datetime, timezone, timedelta
import requests
from requests.exceptions import HTTPError
from rich.console import Console
from atc_del_simulator import AdsConfig

AEROAPI_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
AEROAPI_STD_SET_SIZE = 15
AVWX_BASE_URL = "https://avwx.rest/api"


def fetch_departures(ads_config: AdsConfig, icao, number, traffic_type):
    """Fetches the departures for a given ICAO for a random 4h time period and specified number of results and type"""
    aeroapi_session: requests.Session = ads_config.get_property("aeroapi_session")
    if aeroapi_session:
        zulu_4h_ago = datetime.now(timezone.utc) - timedelta(hours=4)
        zulu_10d_ago = datetime.now(timezone.utc) - timedelta(days=10)
        random_start_time = zulu_10d_ago + ((zulu_4h_ago - zulu_10d_ago) * random.random())
        random_stop_time = random_start_time + timedelta(hours=4)
        params = {
            "max_pages": math.floor(number / AEROAPI_STD_SET_SIZE) + 1,
            "start": random_start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": random_stop_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if traffic_type != "ALL":
            params["type"] = traffic_type
        dep_url = f"{AEROAPI_BASE_URL}/airports/{icao}/flights/departures"
        try:
            # TODO Logging
            dep_response = aeroapi_session.get(url=dep_url, params=params)
            dep_json_response = dep_response.json()
            if "departures" in dep_json_response.keys():
                return dep_json_response["departures"]
        except HTTPError as http_err:
            # TODO replace by logging
            console: Console = ads_config.get_property("rich_console")
            console.print_json(data=params)
            console.print_exception(http_err)
    return []


def fetch_operator(ads_config: AdsConfig, icao):
    """Fetches the details of an operator based on its ICAO code"""
    aeroapi_session: requests.Session = ads_config.get_property("aeroapi_session")
    if aeroapi_session and aeroapi_session.headers.get("x-apikey") and icao:
        op_url = f"{AEROAPI_BASE_URL}/operators/{icao}"
        try:
            # TODO Logging
            op_response = aeroapi_session.get(url=op_url)
            return op_response.json()
        except HTTPError as http_err:
            # TODO replace by logging
            console: Console = ads_config.get_property("rich_console")
            console.print_exception(http_err)
    return {}


def fetch_aircraft(ads_config: AdsConfig, aircraft_type):
    """Fetches the details of an aircraft type"""
    aeroapi_session: requests.Session = ads_config.get_property("aeroapi_session")
    if aeroapi_session and aeroapi_session.headers.get("x-apikey") and aircraft_type:
        at_url = f"{AEROAPI_BASE_URL}/aircraft/types/{aircraft_type}"
        try:
            # TODO Logging
            at_response = aeroapi_session.get(url=at_url)
            return at_response.json()
        except HTTPError as http_err:
            # TODO replace by logging
            console: Console = ads_config.get_property("rich_console")
            console.print_exception(http_err)
    return {}


def fetch_raw_metar(ads_config: AdsConfig, icao):
    """Fetches the current METAR of an airport based on its ICAO code"""
    avwx_session: requests.Session = ads_config.get_property("avwx_session")
    if avwx_session and avwx_session.headers.get("Authorization") and icao:
        metar_url = f"{AVWX_BASE_URL}/metar/{icao}"
        try:
            # TODO Logging
            metar_response = avwx_session.get(url=metar_url)
            metar_json_response = metar_response.json()
            return metar_json_response["raw"] if "raw" in metar_json_response and metar_json_response["raw"] else ""
        except HTTPError as http_err:
            # TODO replace by logging
            console: Console = ads_config.get_property("rich_console")
            console.print_exception(http_err)
    return ""


def get_flight_plans(ads_config: AdsConfig, origin, number, traffic_type, details):
    """Returns a set of flight plans for the user to look at with extra details if requested"""
    flight_plans = []
    operator_cache = {}
    aircraft_cache = {}
    origin_metar = ""
    if details:
        origin_metar = fetch_raw_metar(ads_config=ads_config, icao=origin)
    departures = fetch_departures(ads_config=ads_config, icao=origin, number=number, traffic_type=traffic_type)
    for departure in departures:
        if len(flight_plans) >= number:
            break
        if details:
            if (
                "operator_icao" in departure
                and departure["operator_icao"]
                and not departure["operator_icao"] in operator_cache
            ):
                operator = fetch_operator(ads_config=ads_config, icao=departure["operator_icao"].strip())
                operator_cache[departure["operator_icao"]] = operator
            if (
                "aircraft_type" in departure
                and departure["aircraft_type"]
                and not departure["aircraft_type"] in aircraft_cache
            ):
                aircraft = fetch_aircraft(ads_config=ads_config, aircraft_type=departure["aircraft_type"].strip())
                aircraft_cache[departure["aircraft_type"].strip()] = aircraft
        ident = departure["ident"].strip() if "ident" in departure and departure["ident"] else ""
        aircraft_type = (
            departure["aircraft_type"].strip() if "aircraft_type" in departure and departure["aircraft_type"] else ""
        )
        aircraft_details = (
            aircraft_cache[aircraft_type]
            if "aircraft_type" in departure and aircraft_type and aircraft_type in aircraft_cache
            else ""
        )
        origin_icao = (
            departure["origin"]["code_icao"].strip()
            if "origin" in departure and "code_icao" in departure["origin"] and departure["origin"]["code_icao"]
            else ""
        )
        origin_details = departure["origin"] if "origin" in departure else ""
        origin_raw_metar = origin_metar
        destination_icao = (
            departure["destination"]["code_icao"].strip()
            if "destination" in departure
            and "code_icao" in departure["destination"]
            and departure["destination"]["code_icao"]
            else ""
        )
        destination_details = departure["destination"] if "destination" in departure else ""
        operator_icao = (
            departure["operator_icao"].strip() if "operator_icao" in departure and departure["operator_icao"] else ""
        )
        operator_details = (
            operator_cache[operator_icao]
            if "operator_icao" in departure and operator_icao and operator_icao in operator_cache
            else ""
        )
        route = departure["route"].strip() if "route" in departure and departure["route"] else ""
        squawk = random.randint(100, 6999)
        flight_plan = {
            "ident": ident,
            "aircraft_type": aircraft_type,
            "aircraft_details": aircraft_details,
            "origin_icao": origin_icao,
            "origin_details": origin_details,
            "origin_raw_metar": origin_raw_metar,
            "destination_icao": destination_icao,
            "destination_details": destination_details,
            "operator_icao": operator_icao,
            "operator_details": operator_details,
            "route": route,
            "squawk": squawk,
        }
        flight_plans.append(flight_plan)
    return flight_plans

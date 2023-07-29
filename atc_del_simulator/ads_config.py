import requests
from rich.console import Console
from tinydb import TinyDB


class AdsConfig(object):
    """Class representing the ADS Config with relevant data to be shared across methods"""

    def __init__(self, aeroapi_token="", avwx_token="", database="", verbose=False):
        self.conf = {
            "aeroapi_session": requests.Session(),
            "aeroapi_token": aeroapi_token,
            "avwx_session": requests.Session(),
            "avwx_token": avwx_token,
            "database": database,
            "db_connection": None,
            "details": False,
            "use_cache": False,
            "rich_console": Console(),
            "verbose": verbose,
        }
        self.set_api_token(session_name="aeroapi_session", api_token=aeroapi_token)
        self.set_api_token(session_name="avwx_session", api_token=avwx_token)

    def get_property(self, property_name):
        """Get a property of the config"""
        return self.conf.get(property_name)

    def set_property(self, property_name, property_value):
        """Set a property of the config"""
        if property_name in self.conf:
            self.conf[property_name] = property_value
            return self.conf.get(property_name)
        raise KeyError(f"{property_name} is not a valid configuration property")

    def set_api_token(self, session_name, api_token):
        """Set the API token for different sessions"""
        if session_name == "aeroapi_session":
            self.set_property("aeroapi_token", api_token)
            self.conf["aeroapi_session"].headers.update(
                {"Accept": "application/json; charset=UTF-8", "x-apikey": api_token}
            )
        elif session_name == "avwx_session":
            self.set_property("avwx_token", api_token)
            self.conf["avwx_session"].headers.update(
                {"Accept": "application/json; charset=UTF-8", "Authorization": api_token}
            )

    def start_db(self):
        """Start the SQLite DB"""
        self.set_property("db_connection", TinyDB(self.get_property("database")))

    def validate(self):
        errors = []
        if self.get_property("use_cache") and not self.get_property("database"):
            errors.append("Cache enabled but no database provided.")
        if not self.get_property("use_cache") and not self.get_property("aeroapi_token"):
            errors.append("Cache disabled, but no AeroAPI token set")
        if not self.get_property("use_cache") and self.get_property("details") and not self.get_property("avwx_token"):
            errors.append("Cache disabled and details are enabled, but no AVWX token set")
        return errors

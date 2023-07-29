"""Console script for atc_del_simulator."""
import sys
import random
import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from tinydb import TinyDB, where, Query
from atc_del_simulator import AdsConfig, get_flight_plans, fetch_aircraft, fetch_operator, generate_vfr

pass_ads_config = click.make_pass_decorator(AdsConfig, ensure=True)


@click.group()
@click.option(
    "-a",
    "--aeroapi-token",
    envvar="ADS_AEROAPI_TOKEN",
    help="The API token for the AeroAPI API. Can also be set using the ADS_AEROAPI_TOKEN environment variable.",
)
@click.option(
    "-w",
    "--avwx-token",
    default="",
    envvar="ADS_AVWX_TOKEN",
    help="The API token for the AVWX.rest API. Can also be set using the ADS_AVWX_TOKEN environment variable.",
)
@click.option(
    "-d",
    "--database",
    type=click.Path(exists=True),
    envvar="ADE_DATABASE",
    help="Point to a SQLite database file.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable verbose mode.",
)
@pass_ads_config
def cli(ads_config: AdsConfig, aeroapi_token, avwx_token, database, verbose):
    """Standard CLI for ADS"""
    ads_config.set_api_token(session_name="aeroapi_session", api_token=aeroapi_token)
    ads_config.set_api_token(session_name="avwx_session", api_token=avwx_token)
    ads_config.set_property(property_name="verbose", property_value=verbose)
    if database:
        ads_config.set_property(property_name="database", property_value=database)
        ads_config.start_db()


@cli.command()
@click.argument("origin-icao", required=True)
@click.option(
    "-c/-C",
    "--cache/--no-cache",
    default=False,
    show_default=True,
    help=(
        "Use cache for reading data, must also use `--db` flag on main command to determine the database. When no-cache"
        " is used, information will be pulled from the API and if `--db` is enabled, it will be written to the"
        " SQLite DB."
    ),
)
@click.option(
    "-d/-D",
    "--details/--no-details",
    default=True,
    show_default=True,
    help="Show information about destination airport.",
)
@click.option(
    "-n",
    "--number",
    default=5,
    show_default=True,
    help="Number of flight plans to show.",
)
@click.option(
    "-v", "--vfr-number", default=0, show_default=True, help="Include a number of VFR routes in the training."
)
@click.option(
    "-w",
    "--waypoint",
    default="",
    help="Provide a waypoint that must be part of the route. Only works when `--cache` is enabled.",
)
@pass_ads_config
def route(ads_config: AdsConfig, origin_icao, cache, details, number, vfr_number, waypoint):
    """Fetch and display routes for departures from the provided ICAO"""
    ads_config.set_property("use_cache", cache)
    ads_config.set_property("details", details)
    console: Console = ads_config.get_property("rich_console")
    validation_errors = ads_config.validate()
    if len(validation_errors) > 0:
        console.stderr = True
        console.print("Validation errors:", style="bold red")
        for error in validation_errors:
            console.print(error, style="bold red")
        sys.exit(10)
    vfr_number = vfr_number if vfr_number < number else number
    if ads_config.get_property(property_name="verbose"):
        table = Table(title="Invoked options")
        table.add_column("Option", justify="left")
        table.add_column("Value", justify="right")
        table.add_row("AeroAPI token", ads_config.get_property(property_name="aeroapi_token"))
        table.add_row("AVWX token", ads_config.get_property(property_name="avwx_token"))
        table.add_row(
            "Verbose",
            ":white_check_mark:" if ads_config.get_property(property_name="verbose") else ":x:",
        )
        table.add_row(
            "Use cache",
            ":white_check_mark:" if ads_config.get_property(property_name="use_cache") else ":x:",
        )
        table.add_row("Database", ads_config.get_property("database"))
        table.add_row("Details", ":white_check_mark:" if details else ":x:")
        table.add_row("Number", f"{number}")
        table.add_row("Origin ICAO", origin_icao)
        table.add_row("Waypoint", waypoint)
        console.print(table)
        Prompt.ask("Continue?")
    console.clear()

    with console.status("Loading flight plans..."):
        flight_plans = []
        if number > 0:
            ifr_flight_plans = get_flight_plans(
                ads_config=ads_config,
                origin=origin_icao,
                number=number - vfr_number,
                details=details,
                waypoint=waypoint,
            )
            flight_plans.extend(ifr_flight_plans)
        if vfr_number > 0:
            vfr_flight_plans = generate_vfr(
                ads_config=ads_config, origin=origin_icao, number=vfr_number, details=details
            )
            flight_plans.extend(vfr_flight_plans)
        random.shuffle(flight_plans)
    for flight_plan in flight_plans:
        console.clear()
        flight_rules = "IFR" if flight_plan["route"] and not "VFR" in flight_plan["route"] else "VFR"
        field_table = Table(padding=(0, 0), show_edge=False, show_lines=False, show_header=False)
        field_table.add_column(justify="right", width=15)
        field_table.add_column(justify="left", width=15)
        field_table.add_column(justify="right", width=15)
        field_table.add_column(justify="left", width=15)
        field_table.add_column(justify="right", width=15)
        field_table.add_column(justify="left", width=15)
        field_table.add_row(
            "Callsign",
            flight_plan["ident"],
            "A/C Type",
            flight_plan["aircraft_type"],
            "Flight Rules",
            flight_rules,
        )
        field_table.add_row(
            "Depart",
            flight_plan["origin_icao"],
            "Arrive",
            flight_plan["destination_icao"],
            "Alternate",
            "",
        )
        field_table.add_row("Cruise Alt", "N/A", "Scratchpad", "", "Squawk", f'{flight_plan["squawk"]:04d}')
        route_table = Table(padding=(0, 0), show_edge=False, show_lines=False, show_header=False)
        route_table.add_column(justify="right", width=15)
        route_table.add_column(justify="left", width=75)
        route_table.add_row("Route", flight_plan["route"])
        top_table = Table(
            title=f'Flight Plan - {flight_plan["ident"]}',
            show_header=False,
            title_justify="left",
        )
        top_table.add_column(justify="left")
        top_table.add_row(field_table)
        top_table.add_row(route_table)
        console.print(top_table)
        command = Prompt.ask(
            "Select an action (d)etails or (N)ext" if details else "Press enter to view the (N)ext flight plan",
            choices=["d", "N"] if details else ["N"],
            default="N" if details else "N",
        )

        if details and command == "d":
            with console.status("Loading operator and aircraft details..."):
                flight_plan["operator_details"] = fetch_operator(
                    ads_config=ads_config, icao=flight_plan["operator_icao"].strip()
                )
                flight_plan["aircraft_details"] = fetch_aircraft(
                    ads_config=ads_config, aircraft_type=flight_plan["aircraft_type"].strip()
                )

            operator_callsign = (
                flight_plan["operator_details"]["callsign"] if "callsign" in flight_plan["operator_details"] else ""
            )
            aircraft_details = (
                f'{flight_plan["aircraft_details"]["manufacturer"]} {flight_plan["aircraft_details"]["type"]} -'
                f' {flight_plan["aircraft_details"]["description"]}'
                if "type" in flight_plan["aircraft_details"]
                else ""
            )
            destination_name = (
                f'{flight_plan["destination_details"]["name"]} - {flight_plan["destination_details"]["city"]}'
                if "name" in flight_plan["destination_details"]
                else ""
            )
            data_table = Table(padding=(0, 0), show_edge=False, show_lines=False, show_header=False)
            data_table.add_column(justify="right", width=20)
            data_table.add_column(justify="left", width=20)
            data_table.add_column(justify="right", width=20)
            data_table.add_column(justify="left", width=30)
            data_table.add_row(
                "Dest. ICAO",
                flight_plan["destination_icao"],
                "Dest. Name",
                destination_name,
            )
            data_table.add_row(
                "Operator ICAO",
                flight_plan["operator_icao"],
                "Operator Callsign",
                operator_callsign,
            )
            data_table.add_row(
                "Aircraft Type",
                flight_plan["aircraft_type"],
                "Aircraft Details",
                aircraft_details,
            )
            metar_table = Table(padding=(0, 0), show_edge=False, show_lines=False, show_header=False)
            metar_table.add_column(justify="right", width=20)
            metar_table.add_column(justify="left", width=70)
            metar_table.add_row("Origin METAR", flight_plan["origin_raw_metar"])
            top_table.add_section()
            top_table.add_row(data_table)
            top_table.add_row(metar_table)
            console.clear()
            console.print(top_table)
            Prompt.ask("Press enter to view the (N)ext flight plan", choices=["N"], default="N")


@cli.command()
@click.argument("search-term", required=False, default="")
@pass_ads_config
def stats(ads_config: AdsConfig, search_term):
    """Provided database statistics if there is a DB"""
    console: Console = ads_config.get_property("rich_console")
    if ads_config.get_property("database"):
        database: TinyDB = ads_config.get_property("db_connection")
        departure_table = database.table("departures")
        matching_departures = departure_table.search(
            (where("origin")["code_icao"].matches(f".*{search_term}.*"))
            | (where("destination")["code_icao"].matches(f".*{search_term}.*"))
            | (where("route").matches(f".*{search_term}.*"))
        )
        operator_table = database.table("operators")
        matching_operators = operator_table.search(where("icao").matches(f".*{search_term}.*"))
        aircraft_type_table = database.table("aircraft_types")
        matching_aircraft_types = aircraft_type_table.search(where("type").matches(f".*{search_term}.*"))
        table = Table(title="Database stats")
        table.add_column("Table", justify="left")
        table.add_column("# Records", justify="right")
        table.add_row("departures", f"{len(matching_departures)}")
        table.add_row("operators", f"{len(matching_operators)}")
        table.add_row("aircraft_types", f"{len(matching_aircraft_types)}")
        console.print(table)
    else:
        console.stderr = True
        console.print("No database provided!")
        sys.exit(20)


@cli.command()
@pass_ads_config
def clean(ads_config: AdsConfig):
    """Cleans up the database of invalid items"""
    console: Console = ads_config.get_property("rich_console")
    if ads_config.get_property("database"):
        database: TinyDB = ads_config.get_property("db_connection")
        operator_table = database.table("operators")
        matching_operators = operator_table.remove(Query()["status"].exists())
        aircraft_type_table = database.table("aircraft_types")
        matching_aircraft_types = aircraft_type_table.remove(Query()["status"].exists())
        table = Table(title="Database clean up")
        table.add_column("Table", justify="left")
        table.add_column("# Removed items", justify="right")
        table.add_row("operators", f"{len(matching_operators)}")
        table.add_row("aircraft_types", f"{len(matching_aircraft_types)}")
        console.print(table)
    else:
        console.stderr = True
        console.print("No database provided!")
        sys.exit(20)

"""Console script for atc_del_simulator."""
import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from atc_del_simulator import AdsConfig, get_flight_plans
from time import sleep

pass_ads_config = click.make_pass_decorator(AdsConfig, ensure=True)


@click.group()
@click.option('-a', '--aeroapi-token', required=True, envvar='ADS_AEROAPI_TOKEN', help='The API token for the AeroAPI API. Can also be set using the ADS_AEROAPI_TOKEN environment variable')
@click.option('-w', '--avwx-token', default='', envvar='ADS_AVWX_TOKEN', help='The API token for the AVWX.rest API. Can also be set using the ADS_AVWX_TOKEN environment variable')
@click.option('-v', '--verbose', is_flag=True, default=False, show_default=True, help='Enable verbose mode')
@pass_ads_config
def cli(ads_config: AdsConfig, aeroapi_token, avwx_token, verbose):
    """Standard CLI for ADS"""
    ads_config.set_api_token(session_name='aeroapi_session', api_token=aeroapi_token)
    ads_config.set_api_token(session_name='avwx_session', api_token=avwx_token)
    ads_config.set_property(property_name='verbose', property_value=verbose)


@cli.command()
@click.argument('origin-icao', required=True)
@click.option('-d/-D', '--details/--no-details', default=True, show_default=True, help='Show information about destination airport')
@click.option('-n', '--number', default=5, show_default=True, help='Number of flight plans to show')
@click.option('-t', '--type', 'traffic_type', type=click.Choice(['ALL', 'AIRLINE', 'GA'], case_sensitive=False), default='ALL', show_default=True, help='Select which type of flight plans you would like to see')
@pass_ads_config
def route(ads_config: AdsConfig, origin_icao, details, number, traffic_type):
    """Fetch and display routes for departures from the provided ICAO"""
    console: Console = ads_config.get_property('rich_console')
    if ads_config.get_property(property_name='verbose'):
        table = Table(title='Invoked options')
        table.add_column('Option', justify='left')
        table.add_column('Value', justify='right')
        table.add_row('AeroAPI token', ads_config.get_property(property_name='aeroapi_token'))
        table.add_row('AVWX token', ads_config.get_property(property_name='avwx_token'))
        table.add_row('Verbose', ':white_check_mark:' if ads_config.get_property(property_name='verbose') else ':x:')
        table.add_row('Details', ':white_check_mark:' if details else ':x:')
        table.add_row('Number', '{}'.format(number))
        table.add_row('Origin ICAO', origin_icao)
        table.add_row('Type', traffic_type)
        console.print(table)
    console.clear()
    with console.status('Loading flight plans...'):
        flight_plans = get_flight_plans(ads_config=ads_config, origin=origin_icao, number=number, traffic_type=traffic_type, details=details)
    for flight_plan in flight_plans:
        flight_rules = 'IFR' if flight_plan['route'] else 'VFR'
        field_table = Table(padding=(0,0), show_edge=False, show_lines=False, show_header=False)
        field_table.add_column(justify='right', width=15)
        field_table.add_column(justify='left', width=15)
        field_table.add_column(justify='right', width=15)
        field_table.add_column(justify='left', width=15)
        field_table.add_column(justify='right', width=15)
        field_table.add_column(justify='left', width=15)
        field_table.add_row('Callsign', flight_plan['ident'], 'A/C Type', flight_plan['aircraft_type'], 'Flight Rules', flight_rules)
        field_table.add_row('Depart', flight_plan['origin_icao'], 'Arrive', flight_plan['destination_icao'], 'Alternate', '')
        field_table.add_row('Cruise Alt', 'N/A', 'Scratchpad', '', 'Squawk', str(flight_plan['squawk']))
        route_table = Table(padding=(0,0), show_edge=False, show_lines=False, show_header=False)
        route_table.add_column(justify='right', width=15)
        route_table.add_column(justify='left', width=75)
        route_table.add_row('Route', flight_plan['route'])
        top_table = Table(title='Flight Plan - {}'.format(flight_plan['ident']), show_header=False, title_justify='left')
        top_table.add_column(justify='left')
        top_table.add_row(field_table)
        top_table.add_row(route_table)

        if details:
            operator_callsign = flight_plan['operator_details']['callsign'] if 'callsign' in flight_plan['operator_details'] else ''
            aircraft_details = '{} {} - {}'.format(flight_plan['aircraft_details']['manufacturer'], flight_plan['aircraft_details']['type'], flight_plan['aircraft_details']['description']) if 'type' in flight_plan['aircraft_details'] else ''
            data_table = Table(padding=(0,0), show_edge=False, show_lines=False, show_header=False)
            data_table.add_column(justify='right', width=20)
            data_table.add_column(justify='left', width=20)
            data_table.add_column(justify='right', width=20)
            data_table.add_column(justify='left', width=30)
            data_table.add_row('Dest. ICAO', flight_plan['destination_icao'], 'Dest. Name', flight_plan['destination_name'])
            data_table.add_row('Operator ICAO', flight_plan['operator_icao'], 'Operator Callsign', operator_callsign)
            data_table.add_row('Aircraft Type', flight_plan['aircraft_type'], 'Aircraft Details', aircraft_details)
            metar_table = Table(padding=(0,0), show_edge=False, show_lines=False, show_header=False)
            metar_table.add_column(justify='right', width=20)
            metar_table.add_column(justify='left', width=70)
            metar_table.add_row('Origin METAR', flight_plan['origin_raw_metar'])
            top_table.add_section()
            top_table.add_row(data_table)
            top_table.add_row(metar_table)

        console.print(top_table)
        console.print(Rule())

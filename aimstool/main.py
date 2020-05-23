#!/usr/bin/python3
import sys
import argparse
import requests
import boto3
from getpass import getpass
from typing import List

import aimslib.access.connect
from aimslib.common.types import AIMSException, Duty, Sector
import aimslib.detailed_roster.process as dr

from .freeform import build_freeform
from .roster import roster
from .ical import ical
from .build_csv import build_csv
from . import access

ECREW_LOGIN_PAGE = "https://ecrew.easyjet.com/wtouch/wtouch.exe/verify"


def _heartbeat():
    sys.stderr.write('.')
    sys.stderr.flush()


def online(args) -> int:
    post_func = None
    if not args.user:
        print("Username required.")
        return -1
    try:
        post_func = aimslib.access.connect.connect(
            ECREW_LOGIN_PAGE,
            args.user,
            getpass(),
            _heartbeat)
        changes = aimslib.access.connect.changes(post_func)
        if args.format == "changes":
            if changes:
                print("\nYou have changes.")
            else:
                print("\nNo changes.")
            aimslib.access.connect.logout(post_func)
            return 0
        if changes:
            print(
                "\nCannot continue because you have changes.",
                file=sys.stderr)
            aimslib.access.connect.logout(post_func)
            return -1
        if args.format == "freeform":
            dutylist = access.duties(post_func, -args.months)
            crewlist_map = access.crew(post_func, dutylist)
            print(build_freeform(dutylist, crewlist_map))
        elif args.format == "roster":
            dutylist = access.duties(post_func, args.months)
            print(roster(dutylist))
        elif args.format == "ical":
            dutylist = access.duties(post_func, args.months)
            print(ical(dutylist))
        elif args.format == 'csv':
            dutylist = access.duties(post_func, -args.months)
            crewlist_map = access.crew(post_func, dutylist)
            print(build_csv(dutylist, crewlist_map, args.fo))
        aimslib.access.connect.logout(post_func)
        return 0
    except requests.exceptions.RequestException as e:
        print("\n", e.__doc__, "\n", e.request.url, file=sys.stderr)
        if post_func: aimslib.access.connect.logout(post_func)
        return -1
    except AIMSException as e:
        print("\n", e.__doc__, file=sys.stderr)
        if post_func: aimslib.access.connect.logout(post_func)
        return -2


def offline(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='eu-west-1',
            aws_access_key_id='AKIA5MVEHGMFNPWM5B6I',
            aws_secret_access_key='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'
        )
        table = dynamodb.Table('flights')
        s = f.read()
        dutylist = dr.duties(s)
        dutylist = update_from_flightinfo(table, dutylist)
        if args.format == "roster":
            print(roster(dutylist))
        elif args.format == "ical":
            print(ical(dutylist))
        elif args.format == "freeform":
            crew = dr.crew(s, dutylist)
            print(build_freeform(dutylist, crew))
        elif args.format == "csv":
            crew = dr.crew(s, dutylist)
            print(build_csv(dutylist, crew, args.fo))
    return 0


def update_from_flightinfo(table, dutylist: List[Duty]) -> List[Duty]:
    retval: List[Duty] = []
    for duty in dutylist:
        updated_sectors: List[Sector] = []
        for sec in duty.sectors:
            response = table.get_item(Key={
                'flightid': f'{sec.sched_start:%Y-%m-%d:%H%M}{sec.name}'})
            if 'Item' in response:
                i = response['Item']
                print(i)
                updated_sectors.append(
                    sec._replace(
                        reg = i['reg'],
                        type_ = f"A{i['type_']}"))
            else:
                updated_sectors.append(sec)
        retval.append(duty._replace(sectors=updated_sectors))
    return retval


def _args():
    parser = argparse.ArgumentParser(
        description='Access AIMS data from easyJet servers.')
    parser.add_argument('format',
                        choices=['roster', 'freeform', 'changes', 'ical',
                                 'csv'])
    parser.add_argument('--user', '-u')
    parser.add_argument('--file', '-f')
    parser.add_argument('--months', '-m', type=int, default=1)
    parser.add_argument('--fo', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = _args()
    retval = 0;
    if args.file:
        retval = offline(args)
    else:
        retval = online(args)
    return retval


if __name__ == "__main__":
    retval = main()
    sys.exit(retval)

#!/usr/bin/python3
import sys
import os
import argparse
import requests
from getpass import getpass
from typing import List

import aimslib.access.connect
from aimslib.common.types import AIMSException, Duty, Sector, SectorFlags
import aimslib.detailed_roster.process as dr
import aimslib.access.expanded_roster as er

from aimslib.output.freeform import freeform
from aimslib.output.roster import roster
from aimslib.output.ical import ical
from aimslib.output.csv import csv


def _heartbeat():
    sys.stderr.write('.')
    sys.stderr.flush()


class Changes(Exception):
    "You have changes."


def online(args) -> int:
    post_func = None
    username = args.user or os.environ.get('AIMS_USERNAME')
    if not username:
        print("Username required.", file=sys.stderr)
        return -1
    server = args.server or os.environ.get('AIMS_SERVER')
    if not server:
        print("Please specify server.", file=sys.stderr)
        return -1
    password = args.password or os.environ.get('AIMS_PASSWORD') or getpass()
    retval = 0
    outstr = ""
    try:
        post_func = aimslib.access.connect.connect(
            f"https://{server}/wtouch/wtouch.exe/verify",
            username, password, _heartbeat)
        if aimslib.access.connect.changes(post_func):
            raise Changes
        if args.format == "changes":
            outstr = "No changes."
        elif args.format == "freeform":
            dutylist = er.duties(post_func, -args.months)
            crewlist_map = er.crew(post_func, dutylist)
            outstr = freeform(dutylist, crewlist_map)
        elif args.format == "roster":
            dutylist = er.duties(post_func, args.months)
            outstr = roster(dutylist)
        elif args.format == "ical":
            dutylist = er.duties(post_func, args.months)
            outstr = ical(dutylist)
        elif args.format == 'csv':
            dutylist = er.duties(post_func, -args.months)
            crewlist_map = er.crew(post_func, dutylist)
            outstr = csv(dutylist, crewlist_map, args.fo)
    except Changes:
        output = sys.stdout if args.format == 'changes' else sys.stderr
        print("You have changes.", file=output)
    except requests.exceptions.RequestException as e:
        print(f"\n{e.__doc__}\n  e.request.url", file=sys.stderr)
        retval = -2
    except AIMSException as e:
        print(f"\n{e.__doc__}", file=sys.stderr)
        retval = -3
    finally:
        if post_func: aimslib.access.connect.logout(post_func)
        print(f"\n{outstr}")
        return retval



def offline(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        s = f.read()
        dutylist = dr.duties(s)
        if args.format == "roster":
            print(roster(dutylist))
        elif args.format == "ical":
            print(ical(dutylist))
        elif args.format == "freeform":
            dutylist = update_from_flightinfo(dutylist)
            crew = dr.crew(s, dutylist)
            print(freeform(dutylist, crew))
        elif args.format == "csv":
            dutylist = update_from_flightinfo(dutylist)
            crew = dr.crew(s, dutylist)
            print(csv(dutylist, crew, args.fo))
    return 0


def update_from_flightinfo(dutylist: List[Duty]) -> List[Duty]:
    retval: List[Duty] = []
    ids = []
    for duty in dutylist:
        ids.extend([f'{X.sched_start:%Y%m%dT%H%M}F{X.name}'
                    for X in duty.sectors
                    if X.flags == SectorFlags.NONE])
    try:
        r = requests.post(
            f"https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/default/reg",
            json={'flights': ids})
        r.raise_for_status()
        regntype_map = r.json()
    except requests.exceptions.RequestException:
        return dutylist #if anything goes wrong, just return input
    for duty in dutylist:
        updated_sectors: List[Sector] = []
        for sec in duty.sectors:
            flightid = f'{sec.sched_start:%Y%m%dT%H%M}F{sec.name}'
            if flightid in regntype_map:
                reg, type_ = regntype_map[flightid]
                updated_sectors.append(sec._replace(reg=reg, type_=type_))
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
    parser.add_argument('--password', '-p')
    parser.add_argument('--server', '-s')
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

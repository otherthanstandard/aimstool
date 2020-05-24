#!/usr/bin/python3
import sys
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
            dutylist = er.duties(post_func, -args.months)
            crewlist_map = er.crew(post_func, dutylist)
            print(freeform(dutylist, crewlist_map))
        elif args.format == "roster":
            dutylist = er.duties(post_func, args.months)
            print(roster(dutylist))
        elif args.format == "ical":
            dutylist = er.duties(post_func, args.months)
            print(ical(dutylist))
        elif args.format == 'csv':
            dutylist = er.duties(post_func, -args.months)
            crewlist_map = er.crew(post_func, dutylist)
            print(csv(dutylist, crewlist_map, args.fo))
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
    r = requests.post(
        f"https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/default/reg",
        json={'flights': ids})
    if r.status_code != requests.codes.ok:
        return dutylist
    regntype_map = r.json()
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

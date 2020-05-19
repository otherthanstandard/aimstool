#!/usr/bin/python3
import sys
import argparse
import requests
from getpass import getpass
from typing import List
import os.path

import aimslib.access.connect
from  aimslib.access.cache import TripCache, CrewlistCache
import aimslib.access.brief_roster as Roster
from aimslib.common.types import Duty, NoTripDetails
import aimslib.detailed_roster.process as dr

from .freeform import build_freeform
from .roster import roster
from .ical import ical
from .build_csv import build_csv

CACHE_DIR = os.path.expanduser("~/.cache/")
ECREW_LOGIN_PAGE = "https://ecrew.easyjet.com/wtouch/wtouch.exe/verify"


def _heartbeat():
    sys.stderr.write('.')
    sys.stderr.flush()


def _build_expanded_dutylist(post_func, months: int) -> List[Duty]:
    sparse_dutylist = []
    if months < 0: months += 1
    else: months -= 1
    for r in Roster.retrieve(post_func, months):
        sparse_dutylist.extend(Roster.duties(Roster.parse(r)))
    expanded_dutylist = []
    trip_cache = TripCache(CACHE_DIR + "aimslib.tripcache", post_func)
    last_id = None
    for duty in sorted(sparse_dutylist):
        if duty.trip_id == last_id: continue #avoid duplicates
        last_id = duty.trip_id
        if duty.start is None:
            try:
                expanded_dutylist.extend(trip_cache.trip(duty.trip_id))
            except NoTripDetails:
                print(f"Trip details not found for: {duty.trip_id}",
                      file=sys.stderr)
        else:
            expanded_dutylist.append(duty)
    trip_cache.store()
    return expanded_dutylist


def _crewlist_map(post_func, dutylist):
    crew_cache = CrewlistCache(CACHE_DIR + "aimslib.clcache", post_func)
    crewlist_map = {}
    for duty in dutylist:
        if duty.sectors:
            for sector in duty.sectors:
                if not sector.crewlist_id: continue
                crewlist = crew_cache.crewlist(sector.crewlist_id)
                crewlist_map[sector.crewlist_id] = crewlist
    crew_cache.store()
    return crewlist_map


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
            dutylist = _build_expanded_dutylist(post_func, -args.months)
            crewlist_map = _crewlist_map(post_func, dutylist)
            print(build_freeform(dutylist, crewlist_map))
        elif args.format == "roster":
            dutylist = _build_expanded_dutylist(post_func, args.months)
            print(roster(dutylist))
        elif args.format == "ical":
            dutylist = _build_expanded_dutylist(post_func, args.months)
            print(ical(dutylist))
        elif args.format == 'csv':
            dutylist = _build_expanded_dutylist(post_func, -args.months)
            crewlist_map = _crewlist_map(post_func, dutylist)
            print(build_csv(dutylist, crewlist_map))
        aimslib.access.connect.logout(post_func)
        return 0
    except requests.exceptions.RequestException as e:
        print("\n", e.__doc__, "\n", e.request.url, file=sys.stderr)
        if post_func: aimslib.access.connect.logout(post_func)
        return -1


def offline(args) -> int:
    with open(args.file, encoding="utf-8") as f:
        s = f.read()
        dutylist = dr.duties(s)
        if args.format == "roster":
            print(roster(dutylist))
        elif args.format == "ical":
            print(ical(dutylist))
        elif args.format == "freeform":
            crew = dr.crew(s, dutylist)
            print(build_freeform(dutylist, crew))
        elif args.format == "csv":
            crew = dr.crew(s, dutylist)
            print(build_csv(dutylist, crew))
    return 0


def _args():
    parser = argparse.ArgumentParser(
        description='Access AIMS data from easyJet servers.')
    parser.add_argument('format',
                        choices=['roster', 'freeform', 'changes', 'ical',
                                 'csv'])
    parser.add_argument('--user', '-u')
    parser.add_argument('--file', '-f')
    parser.add_argument('--months', '-m', type=int, default=1)
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

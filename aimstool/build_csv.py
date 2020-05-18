import csv
import io
from typing import List, Dict

from aimslib.common.types import Duty, CrewMember, SectorFlags


def build_csv(duties: List[Duty], crews: Dict[str, List[CrewMember]]
) -> str:
    output = io.StringIO(newline='')
    fieldnames = ['act_start', 'act_finish', 'from_', 'to', 'reg', 'type', 'crew']
    writer = csv.DictWriter(output, fieldnames=fieldnames,extrasaction='ignore')
    writer.writeheader()
    for duty in duties:
        if not duty.sectors: continue
        for sector in duty.sectors:
            if (sector.flags != SectorFlags.NONE or
                not (sector.act_start and sector.act_finish)): continue
            sec_dict = sector._asdict()
            crewlist = crews[sector.crewlist_id]
            crewstr = "; ".join([f"{X[1]}:{X[0]}" for X in crewlist])
            sec_dict['type'] = ''
            if (len(sector.crewlist_id) > 3
                and sector.crewlist_id[-3:] in ("319", "320", "321")):
                sec_dict['type'] = f"A{sector.crewlist_id[-3:]}"
            sec_dict['crew'] = crewstr
            writer.writerow(sec_dict)
    output.seek(0)
    return output.read()

from dataclasses import dataclass
from typing import List
from .utils import format_references
import re


@dataclass
class Reference:
    MAP_TYPES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 23, 24]
    TEXT_TYPES = [14, 15, 16, 17, 18]
    ART_TYPES = [19, 20, 21]

    id_placename: int
    name_shorter: str
    pagenumbers: str
    id_sdrtype: int
    type: str = ""

    def __post_init__(self):
        if self.id_sdrtype in self.MAP_TYPES:
            self.type = "map"
        elif self.id_sdrtype in self.ART_TYPES:
            self.type = "artwork"
        elif self.id_sdrtype in self.TEXT_TYPES:
            self.type = "text"

        # de-duplicate and sort pagenumbers from multiple uses of SDR per placename
        # TODO: fancier aggregation attempt, to handle things like "107, 107-108, ..."
        if self.pagenumbers:
            pns = self.pagenumbers
            # pns_deduped = set([e.strip() for e in pns])
            # print(pns_deduped)
            # # TODO: numeric sort? String may not have numeric page numbers
            # pns_sorted = sorted(pns_deduped)
            self.pagenumbers = pns

    sql = """
    SELECT 
    id_placename,
    TRIM(name_shorter) AS name_shorter,
    GROUP_CONCAT(TRIM(pagenumbers)),
    MIN(id_sdrtype)
    FROM (
        SELECT placename.id_placename, sdr.name_shorter, NULLIF(p2.pagenumbers, '') AS pagenumbers, id_sdrtype
        FROM placename
        LEFT JOIN placename_altname p2 ON (placename.id_placename = p2.id_pn_a)
        INNER JOIN sdr ON (p2.id_sdr = sdr.id)
        WHERE p2.output_use=1

        UNION 
        SELECT placename.id_placename, sdr.name_shorter, NULLIF(p2.pagenumbers, '') AS pagenumbers, id_sdrtype
        FROM placename
        LEFT JOIN placename_location p2 ON (placename.id_placename = p2.id_placename)
        INNER JOIN sdr ON (p2.id_sdr = sdr.id)
        WHERE p2.output_use = 1

        UNION 
        SELECT placename.id_placename, sdr.name_shorter, NULLIF(p2.pagenumbers, '') AS pagenumbers, id_sdrtype
        FROM placename
        LEFT JOIN placename_description p2 ON (placename.id_placename = p2.id_placename)
        INNER JOIN sdr ON (p2.id_sdr = sdr.id)
        WHERE p2.output_use = 1

        UNION 
        SELECT placename.id_placename, sdr.name_shorter, NULLIF(p2.pagenumbers, '') AS pagenumbers, id_sdrtype
        FROM placename
        LEFT JOIN placename_laterdev p2 ON (placename.id_placename = p2.id_placename)
        INNER JOIN sdr ON (p2.id_sdr = sdr.id)
        WHERE p2.output_use = 1
    ) AS ref
    -- no duplicate SDRs per placename (UNION removes duplicates but evaluating using all fields)
    GROUP BY id_placename, name_shorter
    """


@dataclass
class Place:
    id: int
    name: str
    description: str
    study_areas: list
    maps: List[Reference]
    texts: List[Reference]
    artwork: List[Reference]
    main_text: str = ""
    plate: int = None
    grid: str = ""
    name_invented: bool = False
    name_indigenous: bool = False
    status: str = ""

    @property
    def output_name(self):
        cleaned_name = re.sub(r'\[.*?\]', '', self.name)

        # Comment these two lines if special invented treatment not desired
        # if self.name_invented is True:
        #     cleaned_name = f"{self.name}"
        if self.name_indigenous is True:
            cleaned_name = f'**_{cleaned_name}_**'
        return cleaned_name.strip()

    @property
    def references_output(self):
        return format_references("Source", self.maps + self.texts + self.artwork)

    sql = """
SELECT placename.id_placename,
pa2.name AS placename,
pa2.invented,
pa2.id_language,
current_status_type,
description,
sa_bronx, sa_brooklyn, sa_harbor_lower, sa_harbor_upper, sa_lis, sa_manhattan,
sa_nassau, sa_newjersey, sa_queens, sa_statenisland, sa_westchester
FROM placename
INNER JOIN placename_altname pa2 ON (placename.id_placename = pa2.id_pn_a AND pa2.canonical = 1)
    """

import argparse
import csv
from datetime import datetime
from dotenv import dotenv_values
from operator import attrgetter
from pathlib2 import Path
from includes.database import Database
from includes.place import Place, Reference
from includes.utils import (
    extant_dir,
    extant_file,
    get_markdown_files,
    get_place,
    truthy,
    update_places,
)
import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path
import re

# 1. SETUP

VERSION = 2 # markdown file draft
ID_LENAPE = 3
# ("1"=>"extant", "2"=>"disappeared", "3"=>"created", "4"=>"post-1609 natural")
STATUS_LABELS = {1: "", 2: "†", 3: "‡", 4: "≈", 5: "⤴"}
STUDY_AREAS = [
    ("sa_bronx", "Bronx"),
    ("sa_brooklyn", "Brooklyn"),
    ("sa_harbor_lower", "Lower harbor"),
    ("sa_harbor_upper", "Upper harbor"),
    ("sa_lis", "Long Island Sound"),
    ("sa_manhattan", "Manhattan"),
    ("sa_nassau", "Nassau"),
    ("sa_newjersey", "New Jersey"),
    ("sa_queens", "Queens"),
    ("sa_statenisland", "Staten Island"),
    ("sa_westchester", "Westchester"),
]

envfile = Path(__file__).resolve().parents[1] / 'lucy.env'
print(envfile)
load_dotenv(dotenv_path=envfile)

# Retrieve the database configuration parameters from environment variables
config = {
    "DBHOST": os.getenv("DBHOST"),
    "DBPORT": os.getenv("DBPORT"),
    "DBNAME": os.getenv("DBNAME"),
    "DBUSER": os.getenv("DBUSER"),
    "DBPASS": os.getenv("DBPASS"),
}

# Retrieve the values from the config dictionary
dbhost = config["DBHOST"]
dbport = config["DBPORT"]
dbname = config["DBNAME"]
dbuser = config["DBUSER"]
dbpass = config["DBPASS"]

# Print the retrieved values to debug
print("DBHOST:", dbhost)
print("DBPORT:", dbport)
print("DBNAME:", dbname)
print("DBUSER:", dbuser)
print("DBPASS:", dbpass)


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    "shapefile", type=extant_file, help="Path to input placename features shapefile"
)
parser.add_argument(
    "markdown-dir",
    type=extant_dir,
    help="Path to directory of markdown files with place id in each filename",
)
parser.add_argument(
    "-o",
    "--output",
    help="Path to output markdown. If not specified, shapefile basename and location will be used.",
)
options = vars(parser.parse_args())

shapefile = Path(options.get("shapefile")).expanduser()
markdown_dir = Path(options.get("markdown-dir")).expanduser()
timestr = datetime.now().date().isoformat()
markdown_dir_name = markdown_dir.name

outputfile = Path(
    options.get("output") or f"{markdown_dir.parent}/{markdown_dir_name}_{timestr}.md"
)


def get_study_areas(areas):
    return [a[1][1] for a in zip(areas, sorted(STUDY_AREAS)) if truthy(a[0])]


# 2. INITIAL POPULATION FROM DATABASE

places = []
with Database(config) as db:
    references = [Reference(*row) for row in db.query(Reference.sql)]
    maps = [r for r in references if r.type == "map"]
    texts = [r for r in references if r.type == "text"]
    artwork = [r for r in references if r.type == "artwork"]
    place_results = db.query(Place.sql)
    for placerow in place_results:
        place = Place(
            id=placerow[0],
            name=placerow[1].strip(),
            name_invented=truthy(placerow[2]),
            name_indigenous=(placerow[3] == ID_LENAPE),
            status=STATUS_LABELS.get(placerow[4], ""),
            description=placerow[5] or "",
            study_areas=get_study_areas(placerow[-11:]),
            maps=[m for m in maps if m.id_placename == placerow[0]],
            texts=[t for t in texts if t.id_placename == placerow[0]],
            artwork=[a for a in artwork if a.id_placename == placerow[0]]
        )
        places.append(place)








# 3. POPULATE PLACE TEXTS FROM MARKDOWN FILES

mdfiles = get_markdown_files(markdown_dir, VERSION)
for mdfile in mdfiles:
    with open(mdfile[1], "r", encoding="UTF-8") as f:
        #print ("Working on ", mdfile)
        try: 
            main_text = f.read().strip()
        except Exception as e: 
            print (e)
            print (mdfile)
    places = update_places(places, mdfile[0], "main_text", main_text)

# 4. POPULATE PLATE AND GRID FROM SHAPEFILE

# TODO: Iterate over shapefile and populate plate and grid, matching on place.id
# places = update_places(places, <placeid>, "plate", <plate number>)
# places = update_places(places, <placeid>, "grid", <grid string>)

#place_csv = r"C:\_data\book\a Welikia Atlas\3 - gazetteer\plate_grid_ids\placename_grid_v7_07052022.csv"
#place_csv = r"C:\_data\book\a Welikia Atlas\3 - gazetteer\plate_grid_ids\placename_grid_v7_08142022.csv"
place_csv = r"C:\Users\lroyte\Documents\Bucket_Connect_Welikia\book\a Welikia Atlas\3 - gazetteer\plate_grid\Placenames_v7_grid_06272024.csv"

with open (place_csv) as csv_file:
    csv_reader  = csv.reader(csv_file, delimiter = ',')
    line_count = 0
    for row in csv_reader:
        # skip header
        if line_count == 0:
            #print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
        # expects three columns:  row[0] = Place_id; row[1] = Plate number; row[2] = Grid number
            #if int(row[0]) == 3689: print(row)
            #print(row)
            places = update_places(places, int(row[0]), "plate", int(row[1]))
            places = update_places(places, int(row[0]), "grid", row[2])

#p = get_place(places, "id", 3325)
#print(p)
#print(p.name, p.plate, p.grid, p.references_output)

# 5. OUTPUT

# sort by id
# places.sort(key=attrgetter("id"))
# sort by name
places.sort(key=attrgetter("name"))
# filter by borough
brooklyn_places = [p for p in places if "Brooklyn" in p.study_areas]
# bronx_places = [p for p in places if "Bronx" in p.study_areas]
places = [p for p in places if p.main_text != ""]   # removes all places without markdown text entry
# print(bronx_places[0])

# TODO:
#  - Can't right-align plate/grid in markdown
#  - Move to pypandoc and write to docx and do as much formatting as possible?
#    Or more useful to output text simply here, for further automated processing externally?
with outputfile.open("w", encoding='utf-8') as f:
    for place in places:
        entry = f"""
**{place.output_name}{place.status}** ({", ".join(place.study_areas)})

Plate {place.plate} ({place.grid})

<*start_text*>

{place.main_text}

<*end_text*> id={place.id}

{place.references_output}
"""

        f.write(entry)
        
print ("That's all he wrote, folks!")
print(type(place.references_output))
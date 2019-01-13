from django.core.management.base import BaseCommand
from states.models import State, County
from django.core.files import File
import networkx
import requests
import fiona
import os
import json
import networkx
from glob import glob
import zipfile
from shapely.geometry import shape
from django.contrib.gis.geos import GEOSGeometry
from progress.bar import IncrementalBar

COUNTIES = "https://www2.census.gov/geo/tiger/TIGER2012/COUNTY/tl_2012_us_county.zip"

CHUNK_SIZE = 1024

TMP_UNZIP = "tmp/"

STATES = [
    # ["State Abbreviation", FIPS, Name]
    ["AK", 2, "ALASKA"],
    ["MS", 28, "MISSISSIPPI"],
    ["AL", 1, "ALABAMA"],
    ["MT", 30, "MONTANA"],
    ["AR", 5, "ARKANSAS"],
    ["NC", 37, "NORTH CAROLINA"],
    ["AS", 60, "AMERICAN SAMOA"],
    ["ND", 38, "NORTH DAKOTA"],
    ["AZ", 4, "ARIZONA"],
    ["NE", 31, "NEBRASKA"],
    ["CA", 6, "CALIFORNIA"],
    ["NH", 33, "NEW HAMPSHIRE"],
    ["CO", 8, "COLORADO"],
    ["NJ", 34, "NEW JERSEY"],
    ["CT", 9, "CONNECTICUT"],
    ["NM", 35, "NEW MEXICO"],
    ["DC", 11, "DISTRICT OF COLUMBIA"],
    ["NV", 32, "NEVADA"],
    ["DE", 10, "DELAWARE"],
    ["NY", 36, "NEW YORK"],
    ["FL", 12, "FLORIDA"],
    ["OH", 39, "OHIO"],
    ["GA", 13, "GEORGIA"],
    ["OK", 40, "OKLAHOMA"],
    ["GU", 66, "GUAM"],
    ["OR", 41, "OREGON"],
    ["HI", 15, "HAWAII"],
    ["PA", 42, "PENNSYLVANIA"],
    ["IA", 19, "IOWA"],
    ["PR", 72, "PUERTO RICO"],
    ["ID", 16, "IDAHO"],
    ["RI", 44, "RHODE ISLAND"],
    ["IL", 17, "ILLINOIS"],
    ["SC", 45, "SOUTH CAROLINA"],
    ["IN", 18, "INDIANA"],
    ["SD", 46, "SOUTH DAKOTA"],
    ["KS", 20, "KANSAS"],
    ["TN", 47, "TENNESSEE"],
    ["KY", 21, "KENTUCKY"],
    ["TX", 48, "TEXAS"],
    ["LA", 22, "LOUISIANA"],
    ["UT", 49, "UTAH"],
    ["MA", 25, "MASSACHUSETTS"],
    ["VA", 51, "VIRGINIA"],
    ["MD", 24, "MARYLAND"],
    ["VI", 78, "VIRGIN ISLANDS"],
    ["ME", 23, "MAINE"],
    ["VT", 50, "VERMONT"],
    ["MI", 26, "MICHIGAN"],
    ["WA", 53, "WASHINGTON"],
    ["MN", 27, "MINNESOTA"],
    ["WI", 55, "WISCONSIN"],
    ["MO", 29, "MISSOURI"],
    ["WV", 54, "WEST VIRGINIA"],
]

def download_file(url):
    local_filename = "raws/" + url.split('/')[-1]
    r = requests.get(url, stream=True)
    bar = IncrementalBar("Downloading {}".format(url), max=int(r.headers['Content-length']))
    with open(local_filename, 'wb') as handle:
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            bar.next(len(chunk))
            if chunk:
                handle.write(chunk)
    bar.finish()
    return local_filename


def unzip_file(path):
    with zipfile.ZipFile(path, 'r') as handle:
        handle.extractall(TMP_UNZIP)
    return TMP_UNZIP


class Command(BaseCommand):
    help = "Build Counties + States"

    def _load_states(self):
        bar = IncrementalBar("Loading States into DB", max=len(STATES))

        for (abbr, fips, state) in STATES:
            if State.objects.filter(id=fips): continue
            State.objects.create(
                id=fips,
                code=abbr,
                name=state.title()
            )
            bar.next()

        bar.finish()

    def _load_counties(self):
        zip_location = download_file(COUNTIES)
        unzip_file(zip_location)
        shape_file = glob(TMP_UNZIP + "tl_2012_us_county.shp")[0]
        polygons = fiona.open(shape_file)
        bar = IncrementalBar("Loading Counties", max=len(polygons))

        for polygon in polygons:
            properties = polygon['properties']
            geometry = polygon['geometry']

            bar.next()

            if County.objects.filter(id=properties['GEOID']):
                continue

            if State.objects.filter(id=int(properties['STATEFP'])):
                continue

            County.objects.create(
                id=properties['GEOID'],
                state=State.objects.get(id=int(properties['STATEFP'])),
                name=properties['NAMELSAD'],
                poly=GEOSGeometry(json.dumps(geometry)),
                area_land=properties['ALAND'],
                area_water=properties['AWATER']
            )

        bar.finish()

    def handle(self, *args, **kwargs):
        self._load_states()
        self._load_counties()

from django.core.management.base import BaseCommand
from states.models import State, StateSubsection, CensusBlock
from django.core.files import File
import networkx
import requests
import fiona
import os
import csv
from glob import glob
import zipfile
from shapely.geometry import shape
from django.contrib.gis.geos import Polygon, MultiPolygon
from progress.bar import IncrementalBar

VTD_DATASOURCE = "https://www2.census.gov/geo/tiger/TIGER2012/VTD/"
BG_DATASOURCE = "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/"
BG_VTD_MAP_DATASOURCE = "http://www2.census.gov/geo/docs/maps-data/data/baf/"

CHUNK_SIZE = 1024

TMP_UNZIP = "tmp/"


def download_file(url):
    local_filename = "raws/" + url.split('/')[-1]
    r = requests.get(url, stream=True)
    bar = IncrementalBar("Downloading {}".format(url), max=int(r.headers['Content-length']))
    with open(local_filename, 'wb') as handle:
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            bar.next(CHUNK_SIZE)
            if chunk:
                handle.write(chunk)
    bar.finish()
    return local_filename


def unzip_file(path):
    with zipfile.ZipFile(path, 'r') as handle:
        handle.extractall(TMP_UNZIP)
    return TMP_UNZIP

class Command(BaseCommand):
    help = "Add a state to the database by state FIPS"

    def add_arguments(self, parser):
        parser.add_argument('state_fips', type=int)
        parser.add_argument('state_code', type=str)
        parser.add_argument('state_name', type=str)

    def _load_vtd(self, state_fips):
        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}tl_2012_{fips}_vtd10.zip".format(api=VTD_DATASOURCE, fips=state_fips))
        unzip_file(zip_location)
        shape_file = glob(TMP_UNZIP + "*.shp")[0]
        polygons = fiona.open(shape_file)

        bar = IncrementalBar("Loading Voting Districts", max=len(polygons))

        for polygon in polygons:
            properties = polygon['properties']
            geometry = polygon['geometry']

            if geometry['type'] == 'MultiPolygon':
                gisPoly = MultiPolygon(geometry['coordinates'])
            else:
                gisPoly = Polygon(geometry['coordinates'])

            newSubsection = StateSubsection(
                id=properties['VTDST10'],
                state=state,
                name=properties['NAMELSAD10'],
                county=int(properties['COUNTYFP10']),
                multi_polygon=geometry['type'] == 'MultiPolygon',
                is_precinct=(not 'WV' in properties['VTDST10']),
                land_mass=properties['ALAND10'],
                water_mass=properties['AWATER10'],
                perimeter=shape(geometry).length,
                area=shape(geometry).area,
                poly=gisPoly
            )
            newSubsection.save()
            bar.next()

        bar.finish()

        # os.rmdir(TMP_UNZIP, ignore_errors=True)

        with open(shape_file, 'rb') as handle:
            state.voting_shape_file = File(handle)
            state.save()

    def _load_bg_vtd_map(self, state_fips):
        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}BlockAssign_ST{fips}_{code}.zip".format(api=BG_VTD_MAP_DATASOURCE, fips=state_fips, code=state.code))
        unzip_file(zip_location)
        csv_file = glob(TMP_UNZIP + "*_VTD.txt")[0]
        with open(csv_file, newline='') as os_handle:
            csv_handle = csv.reader(os_handle)
            next(csv_handle)
            bg_vtd_map = {blockid: vtd for (blockid, countyid, vtd) in csv_handle}

        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}tabblock2010_{fips}_pophu.zip".format(api=BG_DATASOURCE, fips=state_fips))
        unzip_file(zip_location)
        shape_file = glob(TMP_UNZIP + "*.shp")[0]
        polygons = fiona.open(shape_file)

        bar = IncrementalBar("Loading census population data", max=len(polygons))

        for polygon in polygons:
            properties = polygon['properties']
            geometry = polygon['geometry']

            newBg = CensusBlock(
                id=properties['BLOCKID10'],
                subsection=StateSubsection.objects.get(id=bg_vtd_map[properties['BLOCKID10']]),
                population=properties['POP10'],
                housing_units=properties['HOUSING10'],
            )
            
            newBg.save()
            bar.next()

        bar.finish()

    def _create_state_db(self, state_fips, code, name):
        new_state = State(
            id=state_fips,
            code=code.upper(),
            name=name.title()
        )
        new_state.save()

    def handle(self, *args, **options):
        self._create_state_db(options['state_fips'], options['state_code'], options['state_name'])
        self._load_vtd(options['state_fips'])
        self._load_bg_vtd_map(options['state_fips'])
        
        # self._populate_census_db()

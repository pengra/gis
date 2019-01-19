from django.core.management.base import BaseCommand
from states.models import State, StateSubsection, CensusBlock, County
from django.core.files import File
import networkx
import requests
import fiona
import os
import json
import csv
import networkx
from glob import glob
import zipfile
from shapely.geometry import shape
from django.contrib.gis.geos import GEOSGeometry
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
    help = "Add a state to the database by state FIPS"

    def add_arguments(self, parser):
        parser.add_argument('state_fips', type=int)
        parser.add_argument('state_code', type=str)
        parser.add_argument('state_name', type=str)
        parser.add_argument('county_mode', type=int)

    def _load_vtd(self, state_fips):
        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}tl_2012_{fips}_vtd10.zip".format(api=VTD_DATASOURCE, fips=state_fips))
        unzip_file(zip_location)
        shape_file = glob(TMP_UNZIP + "*{}*vtd10.shp".format(state_fips))[0]
        polygons = fiona.open(shape_file)

        bar = IncrementalBar("Loading Voting Districts", max=len(polygons))

        for polygon in polygons:
            properties = polygon['properties']
            geometry = polygon['geometry']

            poly_geos = GEOSGeometry(json.dumps(geometry))

            if geometry['type'] == 'MultiPolygon':
                for poly in poly_geos:
                    newSubsection = StateSubsection(
                        geoid=properties['GEOID10'],
                        state=state,
                        name=properties['NAMELSAD10'],
                        county=int(properties['COUNTYFP10']),
                        has_siblings=True,
                        is_precinct=('A' == properties['VTDI10']),
                        land_mass=properties['ALAND10'],
                        water_mass=properties['AWATER10'],
                        perimeter=poly.length,
                        area=poly.area,
                        poly=poly
                    )
                    newSubsection.save()
            else:
                newSubsection = StateSubsection(
                    geoid=properties['GEOID10'],
                    state=state,
                    name=properties['NAMELSAD10'],
                    county=int(properties['COUNTYFP10']),
                    has_siblings=False,
                    is_precinct=('A' == properties['VTDI10']),
                    land_mass=properties['ALAND10'],
                    water_mass=properties['AWATER10'],
                    perimeter=shape(geometry).length,
                    area=shape(geometry).area,
                    poly=poly_geos
                )
                newSubsection.save()
            bar.next()

        bar.finish()

        # os.rmdir(TMP_UNZIP, ignore_errors=True)

        with open(zip_location, 'rb') as handle:
            state.voting_shape_file = File(handle)
            state.save()

    def _load_bg_vtd_map(self, state_fips):
        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}BlockAssign_ST{fips}_{code}.zip".format(api=BG_VTD_MAP_DATASOURCE, fips=state_fips, code=state.code))
        unzip_file(zip_location)
        csv_file = glob(TMP_UNZIP + "*{}*_VTD.txt".format(state_fips))[0]
        
        with open(csv_file, newline='') as os_handle:
            csv_handle = csv.reader(os_handle)
            next(csv_handle)
            bg_vtd_map = {blockid: vtd for (blockid, countyid, vtd) in csv_handle}

        state = State.objects.get(id=state_fips)
        zip_location = download_file("{api}tabblock2010_{fips}_pophu.zip".format(api=BG_DATASOURCE, fips=state_fips))
        unzip_file(zip_location)
        shape_file = glob(TMP_UNZIP + "*{}*pophu.shp".format(state_fips))[0]
        polygons = fiona.open(shape_file)

        bar = IncrementalBar("Loading census population data", max=len(polygons))

        for polygon in polygons:
            properties = polygon['properties']
            geometry = polygon['geometry']

            newBg = CensusBlock(
                id=properties['BLOCKID10'],
                # subsection=StateSubsection.objects.filter(geoid__endswith=bg_vtd_map[properties['BLOCKID10']]).order_by('-land_mass')[0],
                population=properties['POP10'],
                housing_units=properties['HOUSING10'],
                poly=GEOSGeometry(json.dumps(geometry))
            )

            newBg.save()
            newBg.subsection = StateSubsection.objects.filter(poly__bboverlaps=newBg.poly).order_by('-land_mass')[0]
            newBg.save()

            bar.next()

        bar.finish()

        with open(zip_location, 'rb') as handle:
            state.block_shape_file = File(handle)
            state.save()

    def _create_state_db(self, state_fips, code, name):
        new_state = State(
            id=state_fips,
            code=code.upper(),
            name=name.title()
        )
        new_state.save()

    def _set_populations(self, state_fips):
        state = State.objects.get(id=state_fips)
        subsections = StateSubsection.objects.filter(state=state)
        bar = IncrementalBar("Applying census population data", max=len(subsections))
        for subsection in subsections:
            bar.next()
            subsection.population = sum([_.population for _ in CensusBlock.objects.filter(subsection=subsection)])
            subsection.save()
        bar.finish()

    def _update_county_population(self, state_fips):
        state = State.objects.get(id=state_fips)
        counties = County.objects.filter(state=state)
        bar = IncrementalBar("Applying census population data to counties", max=len(counties))
        for county in counties:
            county.population = sum([_.population for _ in StateSubsection.objects.filter(poly__bboverlaps=county.poly)])
            county.save()
            bar.next()
        bar.finish()


    def _create_graph(self, state_fips, county_mode):
        graph = networkx.Graph()
        
        state = State.objects.get(id=state_fips)
        if county_mode:
            polygons = County.objects.filter(state=state)
        else:
            polygons = StateSubsection.objects.filter(state=state)

        graph.graph['fips'] = state.id
        graph.graph['code'] = state.code
        graph.graph['state'] = state.name
        graph.graph['districts'] = -1
        graph.graph['is_super'] = 0

        bar = IncrementalBar("Creating Graph Representation (Step 1: Nodes + Meta Data)", max=len(polygons))

        rid_map = {}

        # Create Nodes
        for rid, precinct in enumerate(polygons):
            bar.next()
            graph.add_node(
                rid, 
                geoid=precinct.geoid,
                vertexes=precinct.poly.coords,
                dis=-1, 
                pop=precinct.population, 
                name=precinct.name,
                children=[],
                is_super=False,
                super_level=0,
            )
            rid_map[precinct.geoid] = rid
        
        bar.finish()

        # Create Edges
        bar = IncrementalBar("Creating Graph Representation (Step 2: Edges)", max=len(polygons))

        for precinct in polygons:
            for neighbor in polygons.filter(poly__bboverlaps=precinct.poly):
                if precinct.id != neighbor.id:
                    if county_mode:
                        graph.add_edge(rid_map[precinct.id], rid_map[neighbor.id])
                    else:
                        graph.add_edge(rid_map[precinct.geoid], rid_map[neighbor.geoid])

            bar.next()

        bar.finish()

        networkx.write_gpickle(graph, TMP_UNZIP + 'graph_{}.snx'.format(state_fips))
        with open(TMP_UNZIP + 'graph_{}.snx'.format(state_fips), 'rb') as handle:
            state.graph_representation = File(handle)
            state.edges = len(graph.edges)
            state.nodes = len(graph.nodes)
            state.save()
            

    def handle(self, *args, **options):
        self._create_state_db(options['state_fips'], options['state_code'], options['state_name'])
        self._load_vtd(options['state_fips'])
        self._load_bg_vtd_map(options['state_fips'])
        self._set_populations(options['state_fips'])
        self._update_county_population(options['state_fips'])
        self._create_graph(options['state_fips'], options['county_mode'])


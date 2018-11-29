"""
A simple tool for building random precinct maps.

- Read US Census data/Generate random data
- Build precinct node map
- Divide it into n districts quickly

Norton Pengra - nortonjp@uw.edu - github.com/pengra
"""

__VERSION__ = 0.01

import sys
import argparse
import json
import io
import os
import random
from collections import Iterable
import glob

try:
    import requests
    import fiona
    import geopandas
    import networkx
    import shapely
    import plotly
    import plotly.plotly as plt
    import plotly.graph_objs as go
    import plotly.io as pio
    from progress.bar import IncrementalBar
    from progress.spinner import Spinner
except ImportError:
    raise ImportError("Requires 3rd party library, did you do `pip install -r requirements.txt`?")

from util import *

# APIs for geography data.
US_CENSUS_API = "https://www2.census.gov/geo/tiger/TIGER2009/"
# CACHE_API = "https://data.pengra.io/state_gis/"

COLORS = [
    "#f46242", "#f4b841", "#f4f141", "#bada55", "#61f441", "#41f491", "#41f4d9", 
    "#41d0f4", "#4188f4", "#4c41f4", "#9a41f4", "#d341f4", "#f441d0", "#f4417c", 
    "#f44141", "#ffdddd", "#ffe8dd", "#fffedd", "#f3ffdd", "#e2ffdd", "#ddffef",
    "#ddfbff", "#ddebff", "#e0ddff", "#f6ddff", "#ffddf8", "#6b4141", "#6b5241",
    "#6b5d41", "#6b6641", "#5a6b41", "#436b41", "#416b54", "#416b64", "#41616b",
    "#414c6b", "#4b416b", "#58416b", "#66416b", "#6b4150", "#ffffff", "#000000"
]


def is_valid_state(state):
    """
    Check if the passed in state exists in the valid_states.json file.
    """
    log("Validating State...")
    with io.open("buildmap/valid_states.json") as handle:
        valid_states = json.loads(handle.read())
    return state in valid_states

def seed_census_api(state, granularity):
    """
    Build an initial node graph from US Census site.
    """
    log("Downloading state {} data".format(granularity))

    # Get state_id/state and use it to define file/directory names
    state_id, state_name = state.split('_', 1)
    filename = "tl_2009_{}_{}".format(state_id, granularity)
    dirname = "{}/".format(state_id)

    if not os.path.isdir(dirname):
        if not os.path.isfile(filename):
            download_file(US_CENSUS_API + state + "/" + filename + ".zip")
        unzip(filename + ".zip", dirname)
    
    log("Loading state {} data into memory".format(granularity))
    
    shape = fiona.open(dirname + filename + ".shp")
    return shape

def seed_pengra_api(state, granularity):
    """
    Build an initial node graph using personal API.
    """
    raise NotImplementedError("Server still being worked on.")

def seed_blocks(state):
    """
    Build an initial node graph from blocks.
    Data comes from US Census.
    """
    return seed_census_api(state, "tabblock")

def seed_counties(state):
    """
    Build an initial node graph from counties.
    Data comes from US Census.
    """
    return seed_census_api(state, "county")

def connect_nodes(graph):
    """
    Create an adjacency matrix given a set of vertexes.
    First, check if the polygons overlap when projected to the x and y axis.
    In Washington, this check eliminates 50%-96% of all paired polygons depending on granularity.
    Typically, the smaller the granularity, the higher the elimnation rates.
    
    If their projections overlap, start to do the expensive C++ implemented Weiler-Atherton checks.

    ## Notes:
    GIS Alternative (not automatic): http://desktop.arcgis.com/en/arcmap/latest/tools/analysis-toolbox/how-polygonneighbors-analysis-works.htm
    
    ## References:
    The fantastic Algorithm: https://en.wikipedia.org/wiki/Weiler–Atherton_clipping_algorithm

    ## Performance Notes:
    Worst case (everything is connected to everything): o(n^4)
    Best case (no adjacencies): o(n^2) 
    
    Server will execute this code in roughly 40-50% faster than laptop.

    REQUIRES LARGE AMOUNTS OF RAM. Washington state @ block level typically requires 5-6GB of RAM.
    """
    overlappings = 0
    potential_candidates = 0
    failures = 0
    invalids = 0
    merge = 0
    bar = IncrementalBar("[!] Creating Edges...", max=len(graph.nodes.data()))

    def overlaps(polya, polyb):
        return bool(polya.touches(polyb)) or bool(polya.intersects(polyb))

    to_drop = []

    for gid, geo_data in list(graph.nodes.data()):
        bar.next()
        for gid2, geo_data2 in list(graph.nodes.data()):
            # An absolutely disgusting way to skip nodes we've already looked at.
            # data() doesn't support indexing.
            
            if int(gid2) < int(gid): continue
            
            # check if they overlap when projected to 1d
            potential_candidate = (
                (geo_data['min_lon'] <= geo_data2['max_lon'] and 
                geo_data2['min_lon'] <= geo_data['max_lon']) or
                (geo_data['min_lat'] <= geo_data2['max_lat'] and 
                geo_data2['min_lat'] <= geo_data['max_lat'])
            )

            if potential_candidate:
                # Expensive.
                
                if geo_data['geometry']['type'].lower() == 'polygon':
                    polyA = shapely.geometry.Polygon(shapely.geometry.shape(geo_data['geometry']))
                elif geo_data['geometry']['type'].lower() == 'multipolygon':
                    polyA = shapely.geometry.MultiPolygon(shapely.geometry.shape(geo_data['geometry']))

                if geo_data2['geometry']['type'].lower() == 'polygon':
                    polyB = shapely.geometry.Polygon(shapely.geometry.shape(geo_data2['geometry']))
                elif geo_data2['geometry']['type'].lower() == 'multipolygon':
                    polyB = shapely.geometry.MultiPolygon(shapely.geometry.shape(geo_data2['geometry']))

                if gid != gid2 and overlaps(polyA, polyB):
                    
                    # 0 Multipolygons && and all scenarios
                    # if geo_data['geometry']['type'].lower() == geo_data2['geometry']['type'].lower() == 'polygon':
                    overlappings += 1
                    graph.add_edge(gid, gid2)

                    # 2 multipolygons
                    if geo_data['geometry']['type'].lower() == 'multipolygon' and geo_data2['geometry']['type'].lower() == 'multipolygon':
                        merge += 1

                        bandedA = polyA.convex_hull
                        bandedB = polyB.convex_hull

                        if overlaps(bandedA, bandedB):
                            to_drop.append((gid, gid2))

                    # a is multipolygon, b is polygon
                    elif geo_data['geometry']['type'].lower() == 'multipolygon':
                        merge += 1

                        bandedA = polyA.convex_hull

                        if overlaps(bandedA, polyB):
                            to_drop.append((gid, gid2))
                            
                    # b is multipolygon, a is polygon
                    elif geo_data2['geometry']['type'].lower() == 'multipolygon':
                        merge += 1

                        bandedB = polyB.convex_hull

                        if overlaps(polyA, bandedB):
                            to_drop.append((gid, gid2))


            potential_candidates += potential_candidate
            failures += not potential_candidate

    bar.finish()

    bar = IncrementalBar("[!] Merging Multi Polygons...", max=len(to_drop))


    # Merging
    target_consumption_history = {}

    while to_drop:
        (consumer, target) = to_drop.pop()
        originalConsumer, originalTarget = consumer, target
        bar.next()

        for i, (c2, t2) in enumerate(to_drop):
            while c2 in target_consumption_history.keys():
                c2 = target_consumption_history[c2]
            while t2 in target_consumption_history.keys():
                t2 = target_consumption_history[t2]
            
            to_drop[i] = (c2, t2)

        while consumer in target_consumption_history.keys():
            consumer = target_consumption_history[consumer]

        while target in target_consumption_history.keys():
            target = target_consumption_history[target]

        if target != consumer:
            target_consumption_history[target] = consumer
            drop_node(graph, consumer, target)


    graph.graph['ghosts'] = target_consumption_history

    bar.finish()

    graph.remove_edges_from(graph.selfloop_edges())

    log("Found {} potential candidates ({:.2f}% of total)".format(potential_candidates, potential_candidates * 100 / (failures + potential_candidates)))
    log("Found {} overlappings ({:.2f}% of potential candidates)".format(overlappings, overlappings * 100 / potential_candidates))
    log("Found {} candidates for merging".format(merge))
    log("Found {} invalid polygons ({:.2f}% of total)".format(invalids, invalids * 100 / (failures + potential_candidates)))

    return graph

def load_into_graph(shape):
    """
    Take in a fiona shape file and convert it to a graph.
    O(number of polygons * number of vertexes in polygons)
    """
    # The graph
    graph = networkx.Graph(ghosts={})

    bar = IncrementalBar("[!] Loading polygons as nodes...", max=len(shape))
    # Populate a graph with the usual data
    for i, polygon in enumerate(shape):
        # GeoJSON standard formatting
        fid = polygon['id']
        properties = polygon['properties']
        geometry = polygon['geometry']
        coordinates = geometry['coordinates']
        poly_type = geometry['type']

        # Nice to have messages
        bar.next()

        # Sometimes coordinates are nested inside another list.
        # Use generators to avoid killing the computer.

        def flatten_coordinates(iterable):
            for item in iterable:
                if isinstance(item, Iterable) and (len(item) != 2 or not isinstance(item[0], (float, int))):
                    yield from flatten_coordinates(item)
                else:
                    yield item

        coordinates = flatten_coordinates(coordinates)    
        
        # Set mins/maxes to first item in dataset
        # These values are safe because world coordinates
        # are between -180 and 180.
        minimum_long = 999
        maximum_long = -999
        minimum_lat = 999
        maximum_lat = -999
        
        # For calculating averages
        sum_long = 0
        sum_lat = 0
        total = 0

        # make a copy of coordinates
        vertexes = []
        
        # Find min/max
        for vertex in coordinates:
            if len(vertex) != 2:
                print(vertex)
            (longitude, lattitude) = vertex
            
            total += 1
            sum_long += longitude
            sum_lat += lattitude

            # Store as vertex
            vertexes.append((longitude, lattitude))

            # Pythonic way of finding mins/maxes
            minimum_lat = min([minimum_lat, lattitude])
            minimum_long = min([minimum_long, longitude])
            maximum_lat = max([lattitude, maximum_lat])
            maximum_long = max([longitude, maximum_long])

        graph.add_node(
            fid,  # GIS decided indexes.
            geometry=geometry,
            # flatgeometry=coordinates,
            # For quickly determining if a x/y axis projected polygons overlap
            min_lon=minimum_long,
            max_lon=minimum_long,
            min_lat=minimum_lat,
            max_lat=maximum_lat,
            # For determining which polygon is more north/west/east/south
            avg_lon=sum_long / total, 
            avg_lat=sum_lat / total,
            **properties
        )
    
    bar.finish()

    return graph

def draw_graph(graph, name, districts, image=False):
    log("Building Node Trace")
    
    node_traces = []

    for district in range(districts):
        district_nodes = [node for node, props in graph.nodes(data=True) if props.get('district') == district + 1]
        hex_code = '0123456789abcdef'
        if district >= len(COLORS):
            color = '#' + "".join([random.choice(hex_code) for i in range(6)]) # 6 HEX digits
        else:
            color = COLORS[district]
        node_traces.append(
            go.Scattergeo(
                lat=[graph.nodes.get(node)['avg_lat'] for node in district_nodes],
                lon=[graph.nodes.get(node)['avg_lon'] for node in district_nodes],
                mode="markers",
                name="District {}".format(district + 1),
                marker={
                    "size": 10,
                    "line": {"width": 0.9},
                    "color": color
                },
                hoverinfo="text",
            )
        )
    
    log("Building Edge Trace")

    edge_trace = go.Scattergeo(
        locationmode = 'USA-states',
        lat=[],
        lon=[],
        name="Border",
        mode="lines",
        line={
            "width": 2,
            "color": "#888"
        },
        hoverinfo='none',
    )
    
    bar = IncrementalBar('[!] Building Edges...', max=len(graph.edges))

    for i, (polyA, polyB) in enumerate(graph.edges):
        bar.next()

        polyA = graph.nodes.get(polyA)
        polyB = graph.nodes.get(polyB)
        ax, ay = polyA['avg_lat'], polyA['avg_lon']
        bx, by = polyB['avg_lat'], polyB['avg_lon']
        edge_trace['lat'] += (ax, bx, None)
        edge_trace['lon'] += (ay, by, None)
    
    bar.finish()

    figure = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            hovermode="closest",
            xaxis={"showgrid": False, "zeroline": False},
            yaxis={"showgrid": False, "zeroline": False},
            geo={
                "scope": 'usa',
                "showland": True,
                "landcolor": "rgb(250, 250, 250)",
                "subunitcolor": "rgb(217, 217, 217)",
                "countrycolor": "rgb(217, 217, 217)",
                "countrywidth": 0.5,
                "subunitwidth": 0.5
            }
        )
    )
    
    if image:
        log("Create image with name {}".format(name))
        return pio.write_image(figure, '{}.png'.format(name))

    log("Create plotly plot with name {}".format(name))
    return plt.plot(figure, filename=name)

def drop_node(graph, consumer, target):
    """
    given a graph, have the consumer claim the target.
    Stores all data associated with target in target in a dictionary:
    contains: {
        "target_id": **target_data
    }
    if target has "contains" attribute, the data is merged to all same level.
    """

    graph.nodes[consumer].setdefault('contains', {})

    existing_data = graph.nodes[target].get('contains', {})
    if existing_data:
        del graph.nodes[target]['contains']

    graph.nodes[consumer]['contains'][target] = graph.nodes[target]

    for (child, data) in existing_data.items():
        graph.nodes[consumer]['contains'][child] = data

    graph.remove_node(target)

def drop_nodes(graph, pieces):
    """
    Select random points in the graph and have it "consume" other points in the graph.
    """

    graph.remove_edges_from(graph.selfloop_edges())

    if pieces < len(graph.nodes) and pieces > 0:
        drop_count = len(graph.nodes) - pieces
        log("Dropping {} nodes to fulfill pieces requirement".format(drop_count))
        
        # Populate a "bag" of nodes
        # In a list for the sake of indexes
        choices = [str(_) for _ in range(len(graph.nodes))]
        random.shuffle(choices)

        bar = IncrementalBar('[!] Dropping Nodes...', max=drop_count)

        while drop_count > 0:
            
            # get a random node to drop
            drop = choices.pop()

            
            
            # get a list of it's neighbors and select one
            old_edges = graph.edges(drop)
            
            if len(old_edges) == 0:
                continue
            elif len(old_edges) == 1:
                random_index = 0
            else:
                random_index = random.randint(0, len(old_edges) - 1)
            
            for i, edge in enumerate(old_edges):
                # Again, generators don't have indexes
                if i < random_index: continue

                consuming_node = edge[1]
                # Have consuming node inherit all old edges
                for _, other_node in old_edges:
                    # 如果一樣
                    if other_node != consuming_node:
                        graph.add_edge(consuming_node, other_node)
                break

            while drop in graph.graph['ghosts']:
                drop = graph.graph['ghosts'][drop]

            while consuming_node in graph.graph['ghosts']:
                consuming_node = graph.graph['ghosts'][consuming_node]

            drop_count -= len(graph.nodes[drop].get('contains', {}))

            try:
                if consuming_node != drop:
                    graph.graph['ghosts'][drop] = consuming_node
                    drop_node(graph, consuming_node, drop)
            except KeyError:
                import pdb; pdb.set_trace()
            
            bar.next(drop_count)

        bar.finish()
        
    return graph

def cache_network(graph):
    networkx.write_gpickle(graph, "graph_cache.networkx")

def seed_districts(graph, districts):
    """
    A simple procedure that selects n random seed nodes (n = number of districts)
    and then selects neighbors of those seeds and claims them to be of the same
    district.

    Performance Notes:
    o(n^3), but operations are cheap.
    """
    if districts > 1:
        bar = IncrementalBar("[!] Claiming Districts", max=len(graph.nodes))
        graph_pool = [_ for _ in graph.nodes]
        random.shuffle(graph_pool)

        district_sizes = [[1, district] for district in range(1, districts + 1)]

        # Start the district with some seeds
        for district in range(1, districts + 1):
            bar.next()
            seed = graph_pool.pop()
            graph.nodes.get(seed)['district'] = district

        # While there are unclaimed nodes
        while graph_pool:
            last_run = len(graph_pool)
            # Let each district claim a new node
            district_sizes = sorted(district_sizes)
            for i, (size, district) in enumerate(district_sizes):
                round_complete = False
                # Find the nodes that belong to a district
                for node, props in graph.nodes(data=True): 
                    if props.get('district') == district:
                        # Iterate through edges and find an unclaimed neighbor
                        for _, neighbor in graph.edges(node):
                            if neighbor in graph_pool:
                                graph_pool.remove(neighbor)
                                district_sizes[i][0] += 1
                                bar.next()
                                graph.nodes.get(neighbor)['district'] = district
                                round_complete = True
                                break
                    if round_complete: break # Quicker breaking
                if round_complete: break # Quicker breaking

            if len(graph_pool) == last_run:
                for node in graph_pool:
                    graph.remove_node(node)
                break

        bar.finish()

    else:
        for node in graph.nodes():
            graph.nodes.get(node)['district'] = 0
    
    return graph

def weifan_export(graph, name):
    """
    Export all the districts as TSV file.
    <Precinct ID>"\t"<District ID>
    """
    seperator = ", "
    bar = IncrementalBar("[!] Writing Weifan's Format", max=len(graph.nodes))
    with io.open("{}.tsv".format(name), 'w') as handle:
        handle.write("WA_GEO_ID{seperator}ARTIFICIAL_DISTRICT_ID{seperator}SUPER_SET_ID\n".format(seperator=seperator))
        for i, node in enumerate(sorted(graph.nodes())):
            bar.next()
            handle.write("{geoid}{seperator}{district}{seperator}{i}\n".format(geoid=graph.nodes.get(node)['WA_GEO_ID'], district=graph.nodes.get(node)['district'], i=i, seperator=seperator))
            for child_node in graph.nodes.get(node).get('contains', []):
                handle.write("{geoid}{seperator}{district}{seperator}{i}\n".format(geoid=child_node, district=graph.nodes.get(node)['district'], i=i, seperator=seperator))

    bar.finish()
    

def main(args):
    """
    Run script with -h flag for documentation on main.
    """
    # First, validate the map
    if not is_valid_state(args.state):
        raise ValueError("Unknown State: {}".format(args.state))

    if os.path.isfile("graph_cache.networkx") and not args.no_cache:
        log("Detected cached graph")
        graph = networkx.read_gpickle("graph_cache.networkx")

    else:
        log("Building Graph for {}".format(args.state))
        seed_map = None
        
        if args.granularity == "block":
            seed_map = seed_blocks(args.state)
        elif args.granularity == "county":
            seed_map = seed_counties(args.state)
        elif args.granularity == "file":
            target = glob.glob('file_input/*.shp')[0]
            log("Seeding from {}".format(target))
            seed_map = fiona.open(target)

        # Generate a map given seed
        graph = connect_nodes(load_into_graph(seed_map))
        
        # Cache network after edges are built
        cache_network(graph)

    # Start district claiming after dropping nodes
    graph = drop_nodes(seed_districts(graph, args.districts), args.pieces)

    # Output the graph
    if args.output == "plotly" or args.output == "all":
        # Plotly graph
        draw_graph(graph, args.state, args.districts)
    if args.output == "weifan" or args.output == "all":
        # weifan's precinct/district map
        weifan_export(graph, args.state)
    if args.output == "geoJson" or args.output == "all":
        # geoJson output
        pass
    if args.output == "image" or args.output == "all":
        # image output
        draw_graph(graph, args.state, args.districts, True)


if __name__ == "__main__":
    log("Initial Graph Builder Script")
    
    parser = argparse.ArgumentParser(description="""
    A tool that takes in a state and splits it up into n pieces. Piece granularity is defined by the user.
    VERSION: {}
    """.format(__VERSION__))

    # Random Generation Parameters
    parser.add_argument("state", type=str, help="A state code (such as 53_WASHINGTON).")
    parser.add_argument("granularity", default="precinct", choices=["block", "county", "precinct", "file"], type=str, help="How large the initial chunks should be. If file, checks directory file_input/")
    parser.add_argument("output", type=str, choices=["all", "weifan", "geoJson", "image", "plotly"], help="Format of output.")
    parser.add_argument("districts", type=int, help="Number of districts to split the state into.")
    parser.add_argument("-pieces", type=int, default=0, help="Number of pieces to split the state into. Pass nothing to maintain pieces defined by state set. Passing in a value less than the seed data will result in a noop.")
    parser.add_argument("-no-cache", type=bool, help="Execute without using any cache.")

    # Check inputs are valid
    args = parser.parse_args()

    # Set LOGGER verbosity
    VERBOSE = True

    # Run
    main(args)
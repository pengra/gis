from celery.decorators import task
from descartes import PolygonPatch
from django.core.files import File
import random
import fiona
import networkx
import csv

from progress.bar import IncrementalBar

import matplotlib.pyplot as plt

@task()
def build_seed_map(title, seed, districts, multipolygon, iterations, granularity, nonprecinct):
    # Build a seed map
    from states.models import State, StateSubsection, SeedRedistrictMap
    
    state_id = int(seed.split("_")[1])
    state = State.objects.get(id=state_id)

    newSeed = SeedRedistrictMap(
        title=title,
        districts=districts,
        state=state,
        multi_polygon_behavior=multipolygon,
        nonprecinct_behavior=nonprecinct,
        status='seeding',
    )
    
    newSeed.save()

    graph = networkx.read_gpickle(state.graph_representation.path)

    newSeed.current_step = 0
    newSeed.total_steps = len(graph)
    
    newSeed.save()

    if nonprecinct == 'predrop':
        nonprecincts = StateSubsection.objects.filter(state=state, is_precinct=False)
        for nonprecinct in nonprecincts:
            graph.remove_node(nonprecinct.id)

    
    graph = seed_districts(graph, districts, newSeed)

    if nonprecinct == 'postdrop':
        nonprecincts = StateSubsection.objects.filter(state=state, is_precinct=False)
        for nonprecinct in nonprecincts:
            graph.remove_node(nonprecinct.id)

    newSeed.status = 'visualizing'
    newSeed.current_step = 0
    newSeed.total_steps = len(graph)
    newSeed.save()

    visual_path = "visuals/STATE_{}_nx.png".format(state_id)
    graph_path = "visuals/STATE_{}.nx".format(state_id)
    
    networkx.write_gpickle(graph, graph_path)

    figure = plt.figure(figsize=(15,15)) # 15 by 15 inch image
    axis = figure.gca()

    for district in range(districts):
        notated_district = district + 1
        layer = [node for node, data in graph.nodes(data=True) if data.get('district') == notated_district]
        layer_color = "#" + str(hex(random.randint(0, int(0xDDDDDD))))[2:]
        layer_color += "0" * (7-len(layer_color)) # to make it 6 digits
    
        for precinct in layer:
            polygon = StateSubsection.objects.get(id=precinct).poly
            axis.add_patch(PolygonPatch(polygon, fc=layer_color, ec=layer_color, linewidth=0.8, alpha=0.5, zorder=2))
            newSeed.current_step += 1
            newSeed.save()

    axis.axis('scaled')
    plt.savefig(visual_path, dpi=300)

    with open(visual_path, 'rb') as handle:
        newSeed.initial_visualization = File(handle)
        newSeed.save()

    with open(graph_path, 'rb') as handle:
        newSeed.initial_file = File(handle)
        newSeed.save()

    newSeed.status = 'idle'
    newSeed.save()

    build_weifan_export(newSeed.id)

def build_weifan_export(seed_id):
    # Build weifan's export
    
    from states.models import SeedRedistrictMap, StateSubsection
    
    seed = SeedRedistrictMap.objects.get(id=seed_id)

    seed.status = 'visualizing'
    seed.save()

    graph = networkx.read_gpickle(seed.initial_file.path)

    csv_path = "visuals/{}.weifan.csv".format(seed_id)

    with open(csv_path, "w", newline='') as os_handle:
        csv_handle = csv.writer(os_handle, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        # csv_handle.writerow(["US_GEO_ID", "DISTRICT_ID"])
        for node, data in graph.nodes(data=True):
            csv_handle.writerow([node, data['district']])
    
    with open(csv_path, "r") as handle:
        seed.matrix_map = File(handle)
        seed.save()

    seed.status = 'idle'
    seed.save()


@task()
def visualize_from_upload(redistrict_id):
    from states.models import Redistricting, StateSubsection

    redistrict = Redistricting.objects.get(id=redistrict_id)
    seed = redistrict.initial
    seed.current_step = 0
    

    figure = plt.figure(figsize=(15,15)) # 15 by 15 inch image
    axis = figure.gca()

    visual_path = "visuals/redistrict_{}.png".format(redistrict_id)

    district_colors = []

    for district in range(seed.districts):
        layer_color = "#" + str(hex(random.randint(0, int(0xDDDDDD))))[2:]
        layer_color += "0" * (7-len(layer_color)) # to make it 6 digits
        district_colors.append(layer_color)

    with open(redistrict.matrix_map.path, "r") as handle:
        lines = handle.readlines()
        seed.total_steps = len(lines)
        seed.save()
        for row in lines:
            precinct, district = row.split(",")
            district = int(district)
            polygon = StateSubsection.objects.get(id=precinct).poly
            axis.add_patch(PolygonPatch(polygon, fc=district_colors[district], ec=district_colors[district], linewidth=0.8, alpha=0.5, zorder=2))
            seed.current_step += 1
            seed.save()

    axis.axis('scaled')
    plt.savefig(visual_path, dpi=300)

    with open(visual_path, 'rb') as handle:
        redistrict.visualization = File(handle)
        redistrict.save()


@task()
def visualize_map(state_id):
    # Build a state map

    # Circular Import fix
    from states.models import State, StateSubsection

    # Worker

    visual_path = "visuals/STATE_{}.png".format(state_id)
    state = State.objects.get(id=state_id)
    precincts = StateSubsection.objects.filter(state=state, is_precinct=True)

    figure = plt.figure()
    axis = figure.gca()

    color = "#" + str(hex(random.randint(0, int(0xFFFFFF))))[2:]
    color += "0" * (7-len(color)) # to make it 6 digits

    for precinct in precincts:
        polygon = precinct.poly
        axis.add_patch(PolygonPatch(polygon, fc=color, ec=color, alpha=0.5, zorder=2))

    axis.axis('scaled')
    plt.savefig(visual_path, dpi=300)

    with open(visual_path, 'rb') as handle:
        state.fast_visualization = File(handle)
        state.save()


def seed_districts(graph, districts, newSeed):
    """
    A simple procedure that selects n random seed nodes (n = number of districts)
    and then selects neighbors of those seeds and claims them to be of the same
    district.

    Performance Notes:
    o(n^3), but operations are cheap.
    """
    if districts > 1:
        bar = IncrementalBar("Seeding Districts", max=len(graph.nodes))
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
                                newSeed.current_step += 1
                                newSeed.save()
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
            graph.nodes.get(node)['district'] = 1
    
    return graph

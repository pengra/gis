from celery.decorators import task
from descartes import PolygonPatch
from django.core.files import File
import random
import fiona

import matplotlib.pyplot as plt

@task()
def build_seed_map(title, seed, districts, multipolygon, iterations, granularity, nonprecinct):
    # Build a seed map
    from states.models import State, StateSubsection, SeedRedistrictingMap
    
    state_id = int(seed.split("_")[1])
    state = State.objects.get(id=state_id)

    newSeed = SeedRedistrictingMap(
        title=title,
        districts=districts,
        state=state,
    )

    graph = networkx.read_gpickle(state.graph_representation.path)

    if nonprecinct == 'predrop':
        nonprecincts = StateSubsection.objects.filter(state=state, is_precinct=False)
        for nonprecinct in nonprecincts:
            graph.remove_node(nonprecinct.id)

    
    graph = seed_districts(graph, districts)
    visual_path = "visuals/STATE_{}_nx.png".format(state_id)
    figure = plt.figure()
    axis = figure.gca()

    for district in range(districts):
        notated_district = district + 1
        layer = [node for node, data in graph.nodes(data=True) if data.get('district') == notated_district]
        layer_color = "#" + str(hex(random.randint(0, int(0xFFFFFF))))[2:]
        layer_color += "0" * (7-len(color)) # to make it 6 digits
    
        for precinct in layer:
            polygon = StateSubsection.objects.get(id=precinct).poly
            axis.add_patch(PolygonPatch(polygon, fc=color, ec=color, alpha=0.5, zorder=2))

    axis.axis('scaled')
    plt.savefig(visual_path, dpi=300)

    with open(visual_path, 'rb') as handle:
        newSeed.initial_visualization = File(handle)
        newSeed.initial_file = state.graph_representation
        state.save()


@task()
def run_redistricting_algorithm(seed_id):
    # Build a redistricting given a seed_id
    pass

@task()
def visualize_seed(seed_id):
    # Visualize a seed_map
    pass

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

        # from celery.contrib import rdb; rdb.set_trace()

        axis.add_patch(PolygonPatch(polygon, fc=color, ec=color, alpha=0.5, zorder=2))

    axis.axis('scaled')
    plt.savefig(visual_path, dpi=300)

    with open(visual_path, 'rb') as handle:
        state.fast_visualization = File(handle)
        state.save()


def seed_districts(graph, districts):
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
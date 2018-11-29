from celery.decorators import task
from descartes import PolygonPatch
from django.core.files import File
import random
import fiona

import matplotlib.pyplot as plt

@task()
def build_seed_map(title, seed, districts, multipolygon, iterations, granularity):
    # Build a seed map
    from states.models import State, SeedRedistrictingMap
    
    state_id = int(seed.split("_")[1])
    state = State.objects.get(id=state_id)

    newSeed = SeedRedistrictingMap(
        title=title,
        districts=districts,
        state=state,
    )

    shape = fiona.open(state.voting_shape_file.path)
    

    # Seed the districts
    # Visualize
    # Save as shp file
    # 

    



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

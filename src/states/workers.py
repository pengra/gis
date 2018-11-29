from celery.decorators import task
from states.models import State, StateSubsection
from descartes import PolygonPatch

from django.core.files import File

import matplotlib.pyplot as plt

@task()
def build_seed_map(state_id):
    # Build a seed map
    pass

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
    visual_path = "visuals/STATE_{}.png".format(state_id)
    state = State.objects.get(id=state_id)
    precincts = StateSubsection.objects.filter(state=state, is_precinct=True)

    figure = plt.figure()
    axis = fig.gca()

    color = "#" + str(hex(random.randint(0, int(0xFFFFFF))))[2:]

    for precinct in precincts:
        polygon = precinct.poly
        
        from celery.contrib import rdb; rdb.set_trace()

        axis.addpatch(PolygonPatch(polygon, fc=color, ec=color, alpha=0.5, zorder=2))
        
    axis.axis('scaled')
    plt.savefig(visual_path)

    with open(visual_path, 'rb') as handle:
        state.fast_visualization = File(handle)
        state.save()
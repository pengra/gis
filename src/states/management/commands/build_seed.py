from django.core.management.base import BaseCommand
from states.models import State, SeedRedistrictMap
from django.core.files import File
from progress.bar import IncrementalBar
import networkx
import random

TMP_UNZIP = "tmp/"

class Command(BaseCommand):
    help = "Create a seed Map to start processing"

    def add_arguments(self, parser):
        parser.add_argument('title', type=str)
        parser.add_argument('state_id', type=int)
        parser.add_argument('districts', type=int)

    def handle(self, *args, **options):
        assert options['districts'] > 1
        state = State.objects.get(id=options['state_id'])
        seed = SeedRedistrictMap(
            title=options['title'],
            districts=options['districts'],
            state=state
        )
        seed.save()
        graph = networkx.read_gpickle(state.graph_representation.path)

        graph = self._seed_districts(graph, seed.districts)

        networkx.write_gpickle(graph, TMP_UNZIP + 'redir_{}_{}.dnx'.format(state.id, seed.id))
        with open(TMP_UNZIP + 'redir_{}_{}.dnx'.format(state.id, seed.id), 'rb') as handle:
            seed.initial_file = File(handle)
            seed.save()
                

    def _seed_districts(self, graph, districts):
        """
        A simple procedure that selects n random seed nodes (n = number of districts)
        and then selects neighbors of those seeds and claims them to be of the same
        district.

        Performance Notes:
        o(n^3), but operations are cheap.
        """
        

        bar = IncrementalBar("Seeding Districts", max=len(graph.nodes))
        graph_pool = [_ for _ in graph.nodes]
        random.shuffle(graph_pool)

        district_sizes = [[1, district] for district in range(1, districts + 1)]

        # Start the district with some seeds
        for district in range(1, districts + 1):
            bar.next()
            
            seed = graph_pool.pop()
            graph.nodes.get(seed)['dis'] = district

        # While there are unclaimed nodes
        while graph_pool:
            last_run = len(graph_pool)
            # Let each district claim a new node
            district_sizes = sorted(district_sizes)
            for i, (size, district) in enumerate(district_sizes):
                round_complete = False
                # Find the nodes that belong to a district
                for node, props in graph.nodes(data=True): 
                    if props.get('dis') == district:
                        # Iterate through edges and find an unclaimed neighbor
                        for _, neighbor in graph.edges(node):
                            if neighbor in graph_pool:
                                graph_pool.remove(neighbor)
                                district_sizes[i][0] += 1
                                bar.next()
                                graph.nodes.get(neighbor)['dis'] = district
                                round_complete = True
                                break
                    if round_complete: break # Quicker breaking
                # if round_complete: break # Quicker breaking

            if len(graph_pool) == last_run:
                for candidate in graph_pool:
                    for _, neighbor in graph.edges(candidate):
                        district = graph.nodes[neighbor].get('dis', -1)
                        if district != -1:
                           graph_pool.remove(candidate)
                           district_sizes[district][0] += 1
                           bar.next()
                           graph.nodes[candidate]['dis'] = district
                           round_complete = True
                           break
                    if round_complete: break
                if round_complete: break

            if len(graph_pool) == last_run:
                # PANIC
                import pdb; pdb.set_trace()

        bar.finish()

        return graph

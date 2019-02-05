import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField, JSONField
from states.workers import visualize_map

# Create your models here.

"""
Grab VTD data here: https://www2.census.gov/geo/tiger/TIGER2010/VTD/2010/
Grab Population/Housing Units of each census block here: https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/
A list of what blocks are in what: https://www.census.gov/geo/maps-data/data/baf.html
    District refers to "VTDST10"

"""



class State(models.Model):

    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100, unique=True)
    
    nodes = models.IntegerField(default=0) # number of nodes in the graph
    edges = models.IntegerField(default=0) # number of edges in the graph

    voting_shape_file = models.FileField(upload_to='state/shp/vtd/', null=True)
    block_shape_file = models.FileField(upload_to='state/shp/bg/', null=True)
    graph_representation = models.FileField(upload_to='state/nx/', null=True)

    def __str__(self):
        return self.name


class County(models.Model):
    id = models.IntegerField(primary_key=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=255) # NAMESLAD

    poly = gis_models.GeometryField()

    population = models.BigIntegerField(null=True)
    area_land = models.BigIntegerField(null=True)
    area_water = models.BigIntegerField(null=True)

    @property
    def geoid(self):
        return self.id

    def __str__(self):
        return self.name


class StateSubsection(models.Model):
    geoid = models.CharField(max_length=255, null=True)

    state = models.ForeignKey(State, on_delete=models.CASCADE)

    name = models.CharField(max_length=255) #namelsad10. Is not necessarily unique.
    county = models.IntegerField()

    has_siblings = models.BooleanField(help_text="has siblings?")
    is_precinct = models.BooleanField() # "VW" not in census_id?

    land_mass = models.BigIntegerField() # ALAND10
    water_mass = models.BigIntegerField() # AWATER10

    perimeter = models.FloatField()
    area = models.FloatField()

    poly = gis_models.GeometryField()

    population = models.BigIntegerField(null=True)

    def __str__(self):
        return self.name

class CensusBlock(models.Model):

    id = models.BigIntegerField(primary_key=True, help_text="id", unique=True) #BLOCKID10
    subsection = models.ForeignKey(StateSubsection, null=True, on_delete=models.CASCADE)
    population = models.IntegerField() #POP10
    housing_units = models.IntegerField() #HOUSING10

    poly = gis_models.GeometryField()

    def __str__(self):
        return str(self.id)

class Run(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey('State', on_delete=models.CASCADE)
    districts = models.PositiveIntegerField()
    running = models.BooleanField()

    @property
    def iterations(self):
        return Event.objects.filter(run=self).count()

    @property
    def last_weight_string(self):
        last = Event.objects.filter(run=self).last()
        if last:
            return ", ".join(["{}={}".format(key, item) for key, item in last.weights.items()])

    @property
    def last_percentages_string(self):
        last = Event.objects.filter(run=self).last()
        if last:
            return ", ".join(["{}={}".format(key, item) for key, item in last.scores['percentages'].items()])

class Event(models.Model):
    run = models.ForeignKey('Run', on_delete=models.SET_NULL, null=True)
    type = models.CharField(
        choices=(
            ('move', 'Move'), 
            ('fail', 'Move Failure'),
            ('weight', 'Weight Update'),
            ('burn start', 'Begin Burn in'),
            ('burn end', 'End Burn in'),
            ('anneal start', 'Begin Linear Simulated Annealing'),
            ('anneal end', 'End Linear Simulated Annealing'),
        ), max_length=13
    )
    weights = JSONField()
    map = ArrayField(
        models.IntegerField(),
    )
    scores = JSONField()

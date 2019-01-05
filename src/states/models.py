import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
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

    poly = gis_models.GeometryField(geography=True)

    population = models.BigIntegerField(null=True)

    def __str__(self):
        return self.name

class CensusBlock(models.Model):

    id = models.BigIntegerField(primary_key=True, help_text="id", unique=True) #BLOCKID10
    subsection = models.ForeignKey(StateSubsection, null=True, on_delete=models.CASCADE)
    population = models.IntegerField() #POP10
    housing_units = models.IntegerField() #HOUSING10

    poly = gis_models.GeometryField(geography=True)

    def __str__(self):
        return str(self.id)

class SeedRedistrictMap(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)

    districts = models.IntegerField()

    state = models.ForeignKey(State, on_delete=models.CASCADE)

    initial_file = models.FileField(upload_to='redist/nx/', null=True)
    
    def __str__(self):
        return self.title

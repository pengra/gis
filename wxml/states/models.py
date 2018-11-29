import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models

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

    voting_shape_file = models.FileField(null=True)
    block_shape_file = models.FileField(null=True)
    block_dictionary = models.FileField(null=True)

    fast_visualization = models.ImageField(null=True)

    def __str__(self):
        return self.name


class StateSubsection(models.Model):

    id = models.CharField(primary_key=True, max_length=255, unique=True) # vtdst10
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=255) #namelsad10. Is not necessarily unique.
    county = models.IntegerField()

    multi_polygon = models.BooleanField()
    is_precinct = models.BooleanField() # "VW" not in census_id?

    land_mass = models.BigIntegerField() # ALAND10
    water_mass = models.BigIntegerField() # AWATER10

    perimeter = models.FloatField()
    area = models.FloatField()

    poly = gis_models.GeometryField(geography=True)

    def __str__(self):
        return self.name

class CensusBlock(models.Model):

    id = models.BigIntegerField(primary_key=True, help_text="id", unique=True) #BLOCKID10
    subsection = models.ForeignKey(StateSubsection, on_delete=models.CASCADE)
    population = models.IntegerField() #POP10
    housing_units = models.IntegerField() #HOUSING10

    def __str__(self):
        return str(self.id)

class SeedRedistrictMap(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

    initial_visualization = models.ImageField()
    initial_file = models.FileField()


class Redistrcting(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4, editable=False)
    queue_index = models.IntegerField(default=1, editable=False)

    initial = models.ForeignKey(SeedRedistrictMap, on_delete=models.CASCADE)
    
    visualization = models.ImageField()
    shape_file = models.FileField()

    steps = models.IntegerField(default=0)
    total_runtime = models.FloatField(default=0)

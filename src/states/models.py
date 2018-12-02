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

    voting_shape_file = models.FileField(upload_to='state/shp/vtd/', null=True)
    block_shape_file = models.FileField(upload_to='state/shp/bg/', null=True)
    block_dictionary = models.FileField(upload_to='state/map/pop/', null=True)
    graph_representation = models.FileField(upload_to='state/nx/', null=True)

    fast_visualization = models.ImageField(upload_to='state/img/', null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        parent_save = super().save(*args, **kwargs)
        if not self.fast_visualization:
            visualize_map.delay(self.id)
        return parent_save


class StateSubsection(models.Model):

    id = models.CharField(primary_key=True, max_length=255, unique=True) # vtdst10
    multi_ids = models.ArrayField(models.IntegerField(), size=10, null=True, help_text="IDs of each polygon inside. Ordered by smallest to largest polygon.")
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

    population = models.BigIntegerField(null=True)

    @property
    def geo_id(self):
        return "{}{}{}".format(self.state.id, self.county, self.id)

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
    title = models.CharField(max_length=255)

    districts = models.IntegerField()

    state = models.ForeignKey(State, on_delete=models.CASCADE)

    initial_visualization = models.ImageField(upload_to='redist/img/', null=True)
    initial_file = models.FileField(upload_to='redist/nx/', null=True)
    shape = models.FileField(upload_to='redist/shp/', null=True)
    matrix_map = models.FileField(upload_to='redist/txt/', null=True)

    nonprecinct_behavior = models.CharField(
        choices=(
            ('predrop', "Drop the non-precincts before creating an adjacency graph"),
            ('postdrop', "Drop the non-precincts after creating an adjacency graph and bridge the gaps"),
            ('ignore', "Treat non-precinct polygons like precinct polygons")
        ),
        max_length=8,
        default='ignore'
    )

    status = models.CharField(
        choices=(
            ("idle", "Idle"),
            ("queued", "Queued"),
            ("seeding", "Building Seed Map"),
            ("running", "Running Weifan's code"),
            ("visualizing", "Visualization via Zack's code"),
            ("statistic", "Statistical tests via Langley's code"),
        ),
        max_length=11,
        default="idle"
    )

    multi_polygon_behavior = models.CharField(
        choices=(
            ('accept', "Treat Multipolygons as polygons"),
            ('tear', "Break apart Multipolygons and combine them again post simulation"),
            ('convexhull', "Clump all polygons that are in the convex hull of a multipolygon"),
        ),
        max_length=len('convexhull')
    )

    def __str__(self):
        return self.title


class Redistricting(models.Model):
    id = models.UUIDField(primary_key = True, default=uuid.uuid4, editable=False)
    queue_index = models.IntegerField(default=1, editable=False)

    initial = models.ForeignKey(SeedRedistrictMap, on_delete=models.CASCADE)
    
    multi_polygon_behavior = models.CharField(
        choices=(
            ('accept', "Treat Multipolygons as polygons"),
            ('tear', "Break apart Multipolygons and combine them again post simulation"),
            ('convexhull', "Clump all polygons that are in the convex hull of a multipolygon"),
        ),
        max_length=len('convexhull')
    )

    visualization = models.ImageField(upload_to='redist/img/', null=True)
    graph = models.FileField(upload_to='redist/nx/', null=True)
    shape_file = models.FileField(upload_to='redist/shp/', null=True)
    matrix_map = models.FileField(upload_to='redist/txt/', null=True)

    steps = models.IntegerField(default=0)
    total_runtime = models.FloatField(default=0)

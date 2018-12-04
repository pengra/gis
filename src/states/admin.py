from django.contrib import admin
from states import models

# Register your models here.

class StateAdmin(admin.ModelAdmin):
    search_fields = (
        'code',
        'name',
        'id'
    )
    list_display = (
        'name',
        'code',
        'id'
    )

class VTDAdmin(admin.ModelAdmin):
    list_filter = ('state', 'has_siblings', 'is_precinct')
    search_fields = (
        'id',
        'geoid',
        'name',
    )
    list_display = (
        'id',
        'name',
        'county',
        'state',
        'has_siblings',
        'is_precinct',
        'land_mass',
        'water_mass',
        'perimeter',
        'area',
        'population',
    )


class CensusAdmin(admin.ModelAdmin):
    list_display = ('id', 'subsection', 'population', 'housing_units')
    search_fields = ('id', 'subsection')
    

admin.site.register(models.State, StateAdmin)
admin.site.register(models.StateSubsection, VTDAdmin)
admin.site.register(models.CensusBlock, CensusAdmin)
admin.site.register(models.SeedRedistrictMap)
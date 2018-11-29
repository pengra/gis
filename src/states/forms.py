from django import forms

class BuildNewMapForm(forms.Form):
    title = forms.CharField()
    seed = forms.CharField() # <new|old>_<FIPS>_|<image_url>
    districts = forms.IntegerField()
    multipolygon = forms.ChoiceField(choices=(
            ('accept', "Treat Multipolygons as polygons"),
            ('tear', "Break apart Multipolygons and combine them again post simulation")
            ('convexhull', "Clump all polygons that are in the convex hull of a multipolygon")
        )) # accept, tear, 
    nonprecinct = forms.ChoiceField(
        choices=(
            ('predrop', "Drop the non-precincts before creating an adjacency graph"),
            ('postdrop', "Drop the non-precincts after creating an adjacency graph and bridge the gaps"),
            ('ignore', "Treat non-precinct polygons like precinct polygons")
        )
    )
    iterations = forms.IntegerField()
    granularity = forms.IntegerField()
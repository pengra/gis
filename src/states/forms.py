from django import forms

class BuildNewMapForm(forms.Form):
    title = forms.CharField()
    seed = forms.CharField() # <new|old>_<FIPS>_|<image_url>
    districts = forms.IntegerField()
    multipolygon = forms.CharField() # accept, tear, convexhull
    iterations = forms.IntegerField()
    granularity = forms.IntegerField()
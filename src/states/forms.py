from django import forms

class InitialForm(forms.Form):
    code = forms.CharField()
    mode = forms.CharField()

class CreateRunForm(forms.Form):
    state = forms.IntegerField() # fips code
    districts = forms.IntegerField() # num of districts

class BulkEventPushForm(forms.Form):
    run = forms.UUIDField() # event id
    file = forms.FileField() # events.pk3

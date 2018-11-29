from django.shortcuts import render
from django.views.generic import TemplateView
from states.models import State
# Create your views here.

class NewMapView(TemplateView):
    template_name = 'states/newmap.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['states'] = State.objects.all()
        return context
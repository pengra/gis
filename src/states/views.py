from django.shortcuts import render
from django.views.generic import TemplateView
from states.models import State
from states.forms import BuildNewMapForm
# Create your views here.

class NewMapView(TemplateView):
    template_name = 'states/newmap.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['states'] = State.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form = BuildNewMapForm(request.POST)
        import pdb; pdb.set_trace()
        return super().post(*args, **kwargs)
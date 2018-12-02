from django.shortcuts import render
from django.views.generic import TemplateView
from states.models import State, SeedRedistrictMap, Redistricting
from states.forms import BuildNewMapForm

from states.workers import build_seed_map

# Create your views here.

class NewMapView(TemplateView):
    template_name = 'states/newmap.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['states'] = State.objects.all()
        context['maps'] = SeedRedistrictMap.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form = BuildNewMapForm(request.POST)
        context = self.get_context_data(*args, **kwargs)
        context['form'] = form

        if form.is_valid():
            if form.cleaned_data['seed'].startswith('new'):
                build_seed_map.delay(**form.cleaned_data)

        return super().render_to_response(context)

class ExistingMapsView(TemplateView):
    template_name = 'states/maps.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['maps'] = SeedRedistrictMap.objects.all()
        return context

class SeedDetailView(TemplateView):
    template_name = 'states/mapdetail.html'

    def get_context_data(self, id, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seed'] = SeedRedistrictMap.objects.get(id=id)
        context['redistrictings'] = Redistricting.objects.get(initial=context['seed']).order_by('queue_index')
        context['latest'] = context['redistrictings'][-1]
        context['total_steps'] = sum([redistricting.steps for redistricting in context['redistrictings']])
        context['total_runtime'] = sum([redistricting.total_runtime for redistricting in context['redistrictings']])
        return context


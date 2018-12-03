from django.shortcuts import render, get_object_or_404
from django.core import serializers
from django.http import JsonResponse
from django.views.generic import TemplateView
from states.models import State, SeedRedistrictMap, Redistricting
from states.forms import BuildNewMapForm, VisualizeSimulation
import json

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from states.workers import build_seed_map, visualize_from_upload

# Create your views here.

def avail_maps_json(request):
    data = serializers.serialize('json', SeedRedistrictMap.objects.all())
    return JsonResponse(json.loads(data), safe=False)


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

@method_decorator(csrf_exempt, name='dispatch')
class SeedDetailView(TemplateView):
    template_name = 'states/mapdetail.html'

    def get_context_data(self, id, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seed'] = get_object_or_404(SeedRedistrictMap, id=id)
        context['redistrictings'] = Redistricting.objects.filter(initial=context['seed']).order_by('queue_index')
        context['latest'] = context['redistrictings'].last()
        context['total_steps'] = sum([redistricting.steps for redistricting in context['redistrictings']])
        context['total_runtime'] = sum([redistricting.total_runtime for redistricting in context['redistrictings']])
        return context

    def post(self, request, *args, **kwargs):
        form = VisualizeSimulation(request.POST, request.FILES)
        context = self.get_context_data(*args, **kwargs)
        context['form'] = form

        if form.is_valid():
            newRedistricting = Redistricting(
                queue_index=context['seed'].next_redist_index,
                initial=context['seed'],
                multi_polygon_behavior=context['seed'].multi_polygon_behavior,
                matrix_map=form.cleaned_data['matrix'],
                steps=form.cleaned_data['steps'],
                total_runtime=form.cleaned_data['runtime'],
            )
            newRedistricting.save()
            visualize_from_upload.delay(newRedistricting.id)

        else: 
            return JsonResponse(form.errors, status=400)

        return super().render_to_response(context)


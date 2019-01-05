from django.core import serializers
from django.http import JsonResponse
from django.views.generic import TemplateView
from states.models import State, SeedRedistrictMap
import json

# Create your views here.

def avail_maps_json(request):
    data = serializers.serialize('json', SeedRedistrictMap.objects.all())
    return JsonResponse(json.loads(data), safe=False)


class HomeView(TemplateView):
    template_name = "states/home.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['content'] = [
            {
                "details": state, 
                "maps": []
            } for state in State.objects.all()
        ]
        return context
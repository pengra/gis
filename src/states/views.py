from django.core import serializers
from django.http import JsonResponse
from states.models import State, SeedRedistrictMap
import json

# Create your views here.

def avail_maps_json(request):
    data = serializers.serialize('json', SeedRedistrictMap.objects.all())
    return JsonResponse(json.loads(data), safe=False)


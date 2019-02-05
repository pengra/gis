
from django.views.generic import TemplateView
from django.http import JsonResponse
from states.models import Event, Run

# from state.models import Run

# Create your views here.

class DataView(TemplateView):
    template_name = "home/data.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['runs'] = Run.objects.all()
        return context

class StateListView(TemplateView):
    template_name = "home/states.html"

class APIView(TemplateView):
    template_name = "home/api.html"

    def post(self, *args, **kwargs):
        return JsonResponse(self.json(*args, **kwargs))

    def json(self, *args, **kwargs):
        return {
            "args": args,
            "kwargs": kwargs
        }
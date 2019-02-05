
from django.views.generic import TemplateView
# from state.models import Run

# Create your views here.

class DataView(TemplateView):
    template_name = "home/data.html"

class StateListView(TemplateView):
    template_name = "home/states.html"
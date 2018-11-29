from django.shortcuts import render
from django.views.generic import TemplateView
from states.models import State
from states.forms import BuildNewMapForm

from states.workers import build_seed_map

# Create your views here.

class NewMapView(TemplateView):
    template_name = 'states/newmap.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['states'] = State.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        form = BuildNewMapForm(request.POST)
        context = self.get_context_data(*args, **kwargs)
        context['form'] = form

        if form.is_valid():
            if form.cleaned_data['seed'].startswith('new'):
                build_seed_map.delay(**form.cleaned_data)

        import pdb; pdb.set_trace()
        return super().render_to_response(context)
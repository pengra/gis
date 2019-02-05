
from django.views.generic import TemplateView
from django.http import JsonResponse
from states.models import Event, Run, State
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from states.forms import InitialForm, CreateRunForm, BulkEventPushForm

import pickle

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

@method_decorator(csrf_exempt, name='dispatch')
class APIView(TemplateView):
    template_name = "home/api.html"

    def valid_code(self, code):
        return code == 'default_code'  # TODO: Change this to os.getenv

    def post(self, request, *args, **kwargs):
        initial = InitialForm(request.POST)
        if initial.is_valid() and self.valid_code(initial.cleaned_data.get('code')):
            mode = initial.cleaned_data.get('mode')
            if mode == 'createrun':
                return self.createrun(request, *args, **kwargs)
            elif mode == 'bulkevent':
                return self.bulkevent(request, *args, **kwargs)
            # return JsonResponse(self.json(*args, **kwargs))
        return JsonResponse({"error": True, "message": "Unknown Operation/Invalid Code"}, status=400)

    def bulkevent(self, request, *args, **kwargs):
        bulkForm = BulkEventPushForm(request.POST, request.FILES)
        if bulkForm.is_valid():
            try:
                run = Run.objects.get(id=bulkForm.cleaned_data['run'])
            except Run.DoesNotExist:
                return JsonResponse({
                    "error": True,
                    "message": "Invalid Run ID"
                }, status=404)
            
        import pdb; pdb.set_trace()

    def createrun(self, request, *arkgs, **kwargs):
        runForm = CreateRunForm(request.POST)
        if runForm.is_valid():
            try:
                state = State.objects.get(id=runForm.cleaned_data['state'])
            except State.DoesNotExist:
                return JsonResponse({
                    "error": True,
                    "message": "Invalid State"
                }, status=404)

            run = Run.objects.create(
                state=state,
                districts=runForm.cleaned_data['districts'],
                running=True
            )
            return JsonResponse({
                "error": False,
                "message": "Run ID Created",
                "id": run.id,
            })

        return JsonResponse({
            "error": True,
            "message": "Invalid Run POST Data",
        }, status=400)
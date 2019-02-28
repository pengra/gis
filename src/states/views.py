
from django.views.generic import TemplateView
from django.http import JsonResponse
from states.models import Event, Run, State, ProcessQueue
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from states.forms import InitialForm, CreateRunForm, BulkEventPushForm
from django.shortcuts import get_object_or_404
from django.core import serializers

import json
import pickle
import threading

# Create your views here.


class DataView(TemplateView):
    template_name = "home/data.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['runs'] = Run.objects.all()
        context['tasks'] = ProcessQueue.objects.filter(
            status='queued').count() + 1
        context['working'] = ProcessQueue.objects.filter(status='running')
        return context


class DataDetailView(TemplateView):
    template_name = "home/dash.html"

    def get_context_data(self, id, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['run'] = get_object_or_404(Run, id=id)
        return context


def data_detail_json(request, id):
    try:
        run = Run.objects.get(id=id)
    except:
        return JsonResponse({
            'error': True,
            'message': 'Invalid Run ID'
        }, status=404)
    events = Event.objects.filter(run=run)

    min_ = request.GET.get('min', 0)
    max_ = request.GET.get('max', len(events))
    step = request.GET.get('step', 1)

    if isinstance(min_, str):
        if min_.isnumeric():
            min_ = int(min_)
        else:
            return JsonResponse({
                'error': True,
                'message': 'Invalid min value'
            }, status=400)

    if isinstance(max_, str):
        if max_.isnumeric():
            max_ = int(max_)
        else:
            return JsonResponse({
                'error': True,
                'message': 'Invalid max value'
            }, status=400)

    if isinstance(step, str):
        if step.isnumeric():
            step = int(step)
        else:
            return JsonResponse({
                'error': True,
                'message': 'Invalid step value'
            }, status=400)

    if max_ - min_ > (PAGE_SIZE_MAX * step):
        max_ = (PAGE_SIZE_MAX * step) + min_

    return JsonResponse({
        'error': False,
        'meta': {
            'min': min_,
            'max': max_,
            'step': step,
        },
        'data': [
            {
                "map": event.map,
                "weights": event.weights,
                "scores": event.scores,
                "type": event.type,
                "d_win": event.democratic_win,
                "r_win": event.republican_win,
            } for event in events[min_:max_:step]
        ]
    }, status=200)


class StateListView(TemplateView):
    template_name = "home/states.html"


def create_events():
    # A terrible way to queue things up. But it'll do the job for this small scale project.
    while not ProcessQueue.objects.filter(status='running'):
        target = ProcessQueue.objects.filter(
            status='queued').order_by('queued').first()
        target.status = 'running'
        target.save()

        run = target.run
        db_events = Event.objects.filter(run=run)
        events = json.loads(target.payload)

        if len(db_events) == 0 and events[0][0] != 'seed':
            target.status = 'fail'
            target.save()
            raise ValueError("No seed to start with")
        if len(db_events):
            seed = db_events.last().map
        for event_type, scores, weights, data in events:
            if event_type == 'seed':
                seed = data
                event_type = 'move'
            elif event_type == 'move':
                seed[data[0]] = data[1]

            Event.objects.create(
                run=run,
                type=event_type,
                weights=weights,
                map=seed,
                scores=scores,
            )

        target.status = 'done'
        target.save()


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
            try:
                events = pickle.loads(bulkForm.cleaned_data['file'].read())
                for log in events:
                    if not (log[0] in ['seed', 'move', 'fail', 'weight', 'burn start', 'burn end', 'anneal start', 'anneal end']):
                        raise pickle.UnpicklingError()
            except pickle.UnpicklingError:
                return JsonResponse({
                    "error": True,
                    "message": "Corrupted/Invalid pk3 file"
                }, status=404)

            # create_events(events, run.id)

            ProcessQueue.objects.create(
                status='queued',
                run=run,
                payload=json.dumps(events)
            )

            threading.Thread(target=lambda: create_events()).start()

            return JsonResponse({
                "error": False,
                "message": "Analyzing Events"
            }, status=202)

        return JsonResponse({
            "error": True,
            "message": "Invalid Event POST Data",
        }, status=400)

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

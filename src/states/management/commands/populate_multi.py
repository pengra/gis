from django.core.management.base import BaseCommand
from states.modes import State, StateSubsection

class Command(BaseCommand):
    help = "Populate a multi_id by state FIPS"

    def add_arguments(self, parser):
        parser.add_argument('state_id', type=int)

    def handle(self, *args, **options):
        state = State.objects.get(id=options['state_id'])
        sections = StateSubsection.objects.filter(state=state).order_by('id')

        multi_id = 0

        for section in sections:
            multi_ids = []
            if section.multi_polygon:
                for _ in section.poly:
                    multi_ids.append(multi_id)
                    multi_id += 1
                section.multi_ids = multi_ids
            else:
                section.multi_ids = [multi_id]
                multi_id += 1
            section.save()
                


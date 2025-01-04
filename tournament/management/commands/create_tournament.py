# tournament/management/commands/create_tournament.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from tournament.models import Tournament, Group, TournamentGroup, Team
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates a new tournament copying team structure from the most recent tournament'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Name of the new tournament')

    def handle(self, *args, **options):
        tournament_name = options['name']
        
        # Get the most recent tournament
        previous_tournament = Tournament.objects.order_by('-start_date').first()
        if not previous_tournament:
            self.stdout.write(
                self.style.ERROR('No previous tournament found to copy structure from')
            )
            return

        try:
            with transaction.atomic():
                # Create new tournament
                new_tournament = Tournament.objects.create(
                    name=tournament_name,
                    start_date=timezone.now().date(),
                    status='ONGOING'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created new tournament: {new_tournament.name}')
                )

                # Get all groups from previous tournament
                previous_tournament_groups = TournamentGroup.objects.filter(
                    tournament=previous_tournament
                ).select_related('group')

                # Create new tournament groups
                for prev_tournament_group in previous_tournament_groups:
                    new_tournament_group = TournamentGroup.objects.create(
                        tournament=new_tournament,
                        group=prev_tournament_group.group
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created tournament group: {new_tournament_group.group.name}'
                        )
                    )

                    # Get teams from previous tournament group
                    previous_teams = Team.objects.filter(
                        tournament_group=prev_tournament_group
                    ).select_related('player1', 'player2')

                    # Create new teams
                    for prev_team in previous_teams:
                        new_team = Team.objects.create(
                            player1=prev_team.player1,
                            player2=prev_team.player2,
                            tournament_group=new_tournament_group,
                            rank=prev_team.rank
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created team: {new_team}'
                            )
                        )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create tournament: {str(e)}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created new tournament {tournament_name} '
                f'with {Team.objects.filter(tournament_group__tournament=new_tournament).count()} teams'
            )
        )
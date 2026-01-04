from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date
from tournament.models import Tournament, Group, TournamentGroup


class TournamentGroupValidationTest(TestCase):
    def setUp(self):
        """Create test groups and tournament"""
        self.groups = [
            Group.objects.create(name=f'Group {i}')
            for i in range(6)
        ]
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            start_date=date(2026, 1, 1),
            status='ONGOING'
        )

    def test_tournament_with_one_group_fails(self):
        """Tournament with only 1 group should fail validation"""
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.groups[0]
        )

        with self.assertRaises(ValidationError) as context:
            self.tournament.validate_group_count()

        self.assertIn('at least 2 groups', str(context.exception))

    def test_tournament_with_two_groups_passes(self):
        """Tournament with 2 groups should pass (backward compatibility)"""
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.groups[0]
        )
        TournamentGroup.objects.create(
            tournament=self.tournament,
            group=self.groups[1]
        )

        # Should not raise
        self.tournament.validate_group_count()

    def test_tournament_with_five_groups_passes(self):
        """Tournament with 5 groups should pass"""
        for i in range(5):
            TournamentGroup.objects.create(
                tournament=self.tournament,
                group=self.groups[i]
            )

        # Should not raise
        self.tournament.validate_group_count()

    def test_tournament_with_six_groups_fails(self):
        """Tournament with 6 groups should fail validation"""
        for i in range(6):
            TournamentGroup.objects.create(
                tournament=self.tournament,
                group=self.groups[i]
            )

        with self.assertRaises(ValidationError) as context:
            self.tournament.validate_group_count()

        self.assertIn('maximum of 5 groups', str(context.exception))

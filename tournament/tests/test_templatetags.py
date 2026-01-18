from django.test import TestCase
from django.template import Context, Template
from tournament.models import Player

class CustomTagsTest(TestCase):
    def test_get_item_filter_with_list(self):
        """Test get_item filter with a list"""
        template = Template('{% load custom_tags %}{{ mylist|get_item:1 }}')
        context = Context({'mylist': ['a', 'b', 'c']})
        output = template.render(context)
        self.assertEqual(output.strip(), 'b')

    def test_get_item_filter_with_dict(self):
        """Test get_item filter with a dictionary"""
        template = Template('{% load custom_tags %}{{ mydict|get_item:"key" }}')
        context = Context({'mydict': {'key': 'value'}})
        output = template.render(context)
        self.assertEqual(output.strip(), 'value')

    def test_get_item_filter_out_of_bounds(self):
        """Test get_item filter with out of bounds index"""
        template = Template('{% load custom_tags %}{{ mylist|get_item:10 }}')
        context = Context({'mylist': ['a', 'b', 'c']})
        output = template.render(context)
        self.assertEqual(output.strip(), 'None')

    def test_sub_filter(self):
        """Test sub filter"""
        template = Template('{% load custom_tags %}{{ 10|sub:3 }}')
        context = Context({})
        output = template.render(context)
        self.assertEqual(output.strip(), '7')

    def test_team_name_tag(self):
        """Test team_name template tag"""
        player1 = Player.objects.create(first_name="John", last_name="Doe")
        player2 = Player.objects.create(first_name="Jane", last_name="Smith")
        
        from tournament.models import Team, Tournament, Group, TournamentGroup
        tournament = Tournament.objects.create(
            name="Test",
            start_date="2024-01-01"
        )
        group = Group.objects.create(name="Test Group")
        group2 = Group.objects.create(name="Test Group 2")
        tournament_group = TournamentGroup.objects.create(
            tournament=tournament,
            group=group
        )
        TournamentGroup.objects.create(
            tournament=tournament,
            group=group2
        )
        team = Team.objects.create(
            player1=player1,
            player2=player2,
            tournament_group=tournament_group
        )
        
        template = Template('{% load custom_tags %}{% team_name team 0 0 4 %}')
        context = Context({'team': team})
        output = template.render(context)
        self.assertIn('John', output)
        self.assertIn('Jane', output)
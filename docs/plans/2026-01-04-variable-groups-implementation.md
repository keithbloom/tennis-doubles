# Variable Group Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable 2-5 groups per tournament with predefined names, add tournament history navigation, and update UI to handle variable group counts.

**Architecture:** Leverage existing flexible data model (Group, TournamentGroup). Add predefined groups via migration, extend UI with 3 new tab colors, create history views for browsing past tournaments with prev/next navigation.

**Tech Stack:** Django 5.1, Tailwind CSS, Alpine.js

---

## Task 1: Create Data Migration for Predefined Groups

**Files:**
- Create: `tournament/migrations/0012_add_predefined_groups.py`

**Step 1: Write the migration**

Create the migration file that adds predefined group names:

```python
# tournament/migrations/0012_add_predefined_groups.py
from django.db import migrations


def create_predefined_groups(apps, schema_editor):
    """Create predefined group names for tournament selection"""
    Group = apps.get_model('tournament', 'Group')

    # Only create groups that don't already exist
    group_names = [
        'Racketeers',
        'Serve-ivors',
        'Smashers',
        'Volleyers',
        'Lobbers',
        'Baseliners',
        'Net Rushers',
        'Groundstrokers',
    ]

    for name in group_names:
        Group.objects.get_or_create(name=name)


def reverse_migration(apps, schema_editor):
    """Remove predefined groups (only if they're not in use)"""
    Group = apps.get_model('tournament', 'Group')
    TournamentGroup = apps.get_model('tournament', 'TournamentGroup')

    # Delete groups that are not associated with any tournament
    unused_groups = Group.objects.exclude(
        id__in=TournamentGroup.objects.values_list('group_id', flat=True)
    )
    unused_groups.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0011_rename_walkover_to_retired'),
    ]

    operations = [
        migrations.RunPython(create_predefined_groups, reverse_migration),
    ]
```

**Step 2: Run migration**

Run: `python manage.py migrate`
Expected: Migration applies successfully, creating 8 predefined groups

**Step 3: Verify groups created**

Run: `python manage.py shell -c "from tournament.models import Group; print(Group.objects.count())"`
Expected: Output shows at least 8 groups

**Step 4: Commit**

```bash
git add tournament/migrations/0012_add_predefined_groups.py
git commit -m "feat: add data migration for predefined groups"
```

---

## Task 2: Add Tournament Model Validation

**Files:**
- Modify: `tournament/models.py:5-33` (Tournament model)
- Create: `tournament/tests/test_tournament_validation.py`

**Step 1: Write the failing test**

```python
# tournament/tests/test_tournament_validation.py
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
```

**Step 2: Run test to verify it fails**

Run: `python manage.py test tournament.tests.test_tournament_validation -v 2`
Expected: Tests FAIL with "AttributeError: 'Tournament' object has no attribute 'validate_group_count'"

**Step 3: Write minimal implementation**

Add validation method to Tournament model:

```python
# tournament/models.py (modify Tournament class)
class Tournament(models.Model):
    STATUS_CHOICES = [
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    ]

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ONGOING'
    )
    groups = models.ManyToManyField('Group', through='TournamentGroup')

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after start date")

        if self.status == 'COMPLETED' and not self.end_date:
            raise ValidationError("End date must be set when tournament is completed")

        # Validate group count if tournament is saved (has an ID)
        if self.pk:
            self.validate_group_count()

    def validate_group_count(self):
        """Validate that tournament has between 2 and 5 groups"""
        group_count = self.tournamentgroup_set.count()

        if group_count < 2:
            raise ValidationError(
                "A tournament must have at least 2 groups."
            )

        if group_count > 5:
            raise ValidationError(
                "A tournament can have a maximum of 5 groups."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
```

**Step 4: Run test to verify it passes**

Run: `python manage.py test tournament.tests.test_tournament_validation -v 2`
Expected: All 4 tests PASS

**Step 5: Run all tournament tests**

Run: `python manage.py test tournament.tests -v 2`
Expected: All existing tests still pass

**Step 6: Commit**

```bash
git add tournament/models.py tournament/tests/test_tournament_validation.py
git commit -m "feat: add 2-5 group validation to Tournament model"
```

---

## Task 3: Extend Tailwind Config with New Tab Colors

**Files:**
- Modify: `tailwind.config.js:41-79`

**Step 1: Add new tab badge colors**

Add 3 new colors to extend.colors and safelist:

```javascript
// tailwind.config.js
const colors = require('tailwindcss/colors')
module.exports = {
  content: ["./tournament/templates/**/*.html", "./tournament/static/**/*.js"],
  theme: {
    extend: {
      colors: {
        "custom-teal": "#09c3a1",
        "custom-green": "#91c768",
        "custom-lime": "#c0dd55",
        "custom-yellow": "#eaf3a5",
        "custom-gray": "#f2f2f2",
        "custom-pink-0": "#ffc983",
        "custom-pink-1": "#ffe6ed",
        "custom-pink-2": "#f283c6",
        "custom-pink-3": "#f47c71",
        "custom-pink-4": "#ff4d85",
        "custom-pink-5": "#f36059",
        "custom-pink-6": "#f05c77",
        "custom-badge-0-0": colors.teal[100],
        "custom-badge-0-1": colors.emerald[50],
        "custom-badge-0-2": colors.cyan[200],
        "custom-badge-0-3": colors.green[100],
        "custom-badge-0-4": colors.blue[50],
        "custom-badge-0-5": colors.teal[200],
        "custom-badge-0-6": colors.lime[100],
        "custom-badge-0-7": colors.teal[50],
        "custom-badge-0-8": colors.cyan[100],
        "custom-badge-0-9": colors.emerald[100],
        "custom-badge-1-0": "#fee2e2",
        "custom-badge-1-1": "#e7e5e4",
        "custom-badge-1-2": colors.pink[50],
        "custom-badge-1-3": "#fecaca",
        "custom-badge-1-4": "#e5e5e5",
        "custom-badge-1-5": "#fef2f2",
        "custom-badge-1-6": colors.rose[200],
        "custom-badge-1-7": colors.pink[100],
        "custom-badge-1-8": colors.stone[200],
        "custom-badge-1-9": colors.rose[50],
        "tab-badge-0": colors.blue[100],
        "tab-badge-1": "#fef2f2",
        "tab-badge-2": colors.green[100],
        "tab-badge-3": colors.purple[100],
        "tab-badge-4": colors.amber[100],
      },
      fontFamily: {
        monofett: ["Monofett", "sans-serif"],
      },
    },
  },
  safelist: [
    "bg-custom-pink-0",
    "bg-custom-pink-1",
    "bg-custom-pink-2",
    "bg-custom-pink-3",
    "bg-custom-pink-4",
    "bg-custom-pink-5",
    "bg-custom-pink-6",
    "bg-custom-badge-0-0",
    "bg-custom-badge-0-1",
    "bg-custom-badge-0-2",
    "bg-custom-badge-0-3",
    "bg-custom-badge-0-4",
    "bg-custom-badge-0-5",
    "bg-custom-badge-0-6",
    "bg-custom-badge-0-7",
    "bg-custom-badge-0-8",
    "bg-custom-badge-0-9",
    "bg-custom-badge-1-0",
    "bg-custom-badge-1-1",
    "bg-custom-badge-1-2",
    "bg-custom-badge-1-3",
    "bg-custom-badge-1-4",
    "bg-custom-badge-1-5",
    "bg-custom-badge-1-6",
    "bg-custom-badge-1-7",
    "bg-custom-badge-1-8",
    "bg-custom-badge-1-9",
    "bg-tab-badge-0",
    "bg-tab-badge-1",
    "bg-tab-badge-2",
    "bg-tab-badge-3",
    "bg-tab-badge-4",
    ],
  plugins: [],
};
```

**Step 2: Commit**

```bash
git add tailwind.config.js
git commit -m "feat: add tab colors for up to 5 groups"
```

---

## Task 4: Update Header Template

**Files:**
- Modify: `tournament/templates/components/header.html:1-10`

**Step 1: Update header to use tournament name**

```html
<!-- tournament/templates/components/header.html -->
{% load static %}
<header class="sticky relative h-32 sm:h-48 md:h-64 w-full bg-cover bg-center"
    style="background-image: url({% static 'img/tennis-background.jpg' %});">
    <div class="absolute inset-0 bg-black opacity-10"></div>
    <div class="relative z-10 flex h-full items-center justify-start px-4">
        <h1 class="font-monofett text-3xl sm:text-3xl md:text-4xl lg:text-7xl text-gray-200 tracking-wider font-thin">
            {{ tournament.name }}
        </h1>
    </div>
</header>
```

**Step 2: Commit**

```bash
git add tournament/templates/components/header.html
git commit -m "feat: update header to show tournament name"
```

---

## Task 5: Pass Tournament Object to Grid Template

**Files:**
- Modify: `tournament/views.py:14-47`
- Modify: `tournament/templates/tournament/grid.html:1-10`

**Step 1: Update TournamentGridView to pass tournament**

```python
# tournament/views.py (modify TournamentGridView)
class TournamentGridView(TemplateView):
    """View for displaying tournament grid"""

    template_name = "tournament/grid.html"

    def get_template_names(self):
        """Return template name based on tournament existence"""
        tournament = (
            Tournament.objects.filter(status="ONGOING", end_date__isnull=True, start_date__lte=datetime.now())
            .order_by("-start_date")
            .first()
        )

        if not tournament:
            return ["tournament/no_tournament.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get latest ongoing tournament
        tournament = (
            Tournament.objects.filter(status="ONGOING", end_date__isnull=True)
            .order_by("-start_date")
            .first()
        )

        if not tournament:
            return context

        # Pass tournament object for header and navigation
        context["tournament"] = tournament

        # Use service to build grid data
        grid_builder = TournamentGridBuilder()
        context["group_data"] = grid_builder.build_grid_data(tournament)
        return context
```

**Step 2: Update grid template to use tournament context**

```html
<!-- tournament/templates/tournament/grid.html (update line 6) -->
{% extends "base.html" %}
{% load custom_tags %}

{% block content %}
<div class="bg-slate-50 container mx-auto">
    {% include "components/header.html" with tournament=tournament %}
    <div class="w-full max-w-3xl md:max-w-5xl lg:max-w-6xl mx-auto p-4"
        x-data="{ activeTab: '{{ group_data.0.group.name }}' }">

        <!-- Rest of template unchanged -->
```

**Step 3: Commit**

```bash
git add tournament/views.py tournament/templates/tournament/grid.html
git commit -m "feat: pass tournament object to grid template"
```

---

## Task 6: Create Tournament Detail View

**Files:**
- Modify: `tournament/views.py:48-55`
- Create: `tournament/tests/test_tournament_detail_view.py`

**Step 1: Write the failing test**

```python
# tournament/tests/test_tournament_detail_view.py
from django.test import TestCase
from django.urls import reverse
from datetime import date
from tournament.models import Tournament, Group, TournamentGroup


class TournamentDetailViewTest(TestCase):
    def setUp(self):
        """Create test tournaments"""
        self.tournament1 = Tournament.objects.create(
            name='Tournament 1',
            start_date=date(2026, 1, 1),
            status='COMPLETED',
            end_date=date(2026, 1, 15)
        )
        self.tournament2 = Tournament.objects.create(
            name='Tournament 2',
            start_date=date(2026, 2, 1),
            status='ONGOING'
        )

        # Create groups for tournaments
        group1 = Group.objects.create(name='Group A')
        group2 = Group.objects.create(name='Group B')

        TournamentGroup.objects.create(tournament=self.tournament1, group=group1)
        TournamentGroup.objects.create(tournament=self.tournament1, group=group2)
        TournamentGroup.objects.create(tournament=self.tournament2, group=group1)
        TournamentGroup.objects.create(tournament=self.tournament2, group=group2)

    def test_tournament_detail_view_shows_specific_tournament(self):
        """View should display the requested tournament"""
        response = self.client.get(
            reverse('tournament_detail', args=[self.tournament1.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tournament 1')
        self.assertIn('tournament', response.context)
        self.assertEqual(response.context['tournament'], self.tournament1)

    def test_tournament_detail_view_404_for_invalid_id(self):
        """View should return 404 for non-existent tournament"""
        response = self.client.get(
            reverse('tournament_detail', args=[9999])
        )

        self.assertEqual(response.status_code, 404)
```

**Step 2: Run test to verify it fails**

Run: `python manage.py test tournament.tests.test_tournament_detail_view -v 2`
Expected: Tests FAIL with "NoReverseMatch" or view doesn't exist

**Step 3: Write minimal implementation**

```python
# tournament/views.py (add new view class)
class TournamentDetailView(TemplateView):
    """View for displaying a specific tournament grid"""

    template_name = "tournament/grid.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tournament_id = self.kwargs.get('tournament_id')

        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            from django.http import Http404
            raise Http404("Tournament not found")

        # Pass tournament object
        context["tournament"] = tournament

        # Use service to build grid data
        grid_builder = TournamentGridBuilder()
        context["group_data"] = grid_builder.build_grid_data(tournament)

        # Add prev/next tournament IDs for navigation
        prev_tournament = (
            Tournament.objects.filter(start_date__lt=tournament.start_date)
            .order_by('-start_date')
            .first()
        )
        next_tournament = (
            Tournament.objects.filter(start_date__gt=tournament.start_date)
            .order_by('start_date')
            .first()
        )

        context["prev_tournament"] = prev_tournament
        context["next_tournament"] = next_tournament

        return context
```

**Step 4: Add URL pattern (temporary for test)**

```python
# tournament/urls.py
from django.urls import path
from tournament import views

urlpatterns = [
    path('teams/', views.teams_by_tournament, name='teams_by_tournament'),
    path('tournament/<int:tournament_id>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
]
```

**Step 5: Run test to verify it passes**

Run: `python manage.py test tournament.tests.test_tournament_detail_view -v 2`
Expected: Both tests PASS

**Step 6: Commit**

```bash
git add tournament/views.py tournament/urls.py tournament/tests/test_tournament_detail_view.py
git commit -m "feat: add tournament detail view for specific tournaments"
```

---

## Task 7: Create Tournament History List View

**Files:**
- Modify: `tournament/views.py:75-85`
- Create: `tournament/tests/test_tournament_history_view.py`

**Step 1: Write the failing test**

```python
# tournament/tests/test_tournament_history_view.py
from django.test import TestCase
from django.urls import reverse
from datetime import date
from tournament.models import Tournament, Group, TournamentGroup


class TournamentHistoryViewTest(TestCase):
    def setUp(self):
        """Create multiple test tournaments"""
        self.tournaments = [
            Tournament.objects.create(
                name=f'Tournament {i}',
                start_date=date(2026, i, 1),
                status='COMPLETED' if i < 3 else 'ONGOING'
            )
            for i in range(1, 5)
        ]

        # Add groups to tournaments
        group = Group.objects.create(name='Test Group')
        for tournament in self.tournaments:
            TournamentGroup.objects.create(tournament=tournament, group=group)

    def test_tournament_history_view_lists_all_tournaments(self):
        """View should list all tournaments in reverse chronological order"""
        response = self.client.get(reverse('tournament_history'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('tournaments', response.context)

        tournaments = list(response.context['tournaments'])
        self.assertEqual(len(tournaments), 4)

        # Verify reverse chronological order (newest first)
        self.assertEqual(tournaments[0].name, 'Tournament 4')
        self.assertEqual(tournaments[3].name, 'Tournament 1')

    def test_tournament_history_view_shows_tournament_details(self):
        """View should display tournament names, dates, and status"""
        response = self.client.get(reverse('tournament_history'))

        for tournament in self.tournaments:
            self.assertContains(response, tournament.name)
```

**Step 2: Run test to verify it fails**

Run: `python manage.py test tournament.tests.test_tournament_history_view -v 2`
Expected: Tests FAIL with "NoReverseMatch" or view doesn't exist

**Step 3: Write minimal implementation**

```python
# tournament/views.py (add new view class)
class TournamentHistoryView(TemplateView):
    """View for displaying list of all tournaments"""

    template_name = "tournament/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all tournaments in reverse chronological order
        tournaments = Tournament.objects.all().order_by('-start_date')

        context["tournaments"] = tournaments

        return context
```

**Step 4: Add URL pattern**

```python
# tournament/urls.py (update)
from django.urls import path
from tournament import views

urlpatterns = [
    path('teams/', views.teams_by_tournament, name='teams_by_tournament'),
    path('tournament/<int:tournament_id>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournaments/', views.TournamentHistoryView.as_view(), name='tournament_history'),
]
```

**Step 5: Run test to verify it passes (will fail on template)**

Run: `python manage.py test tournament.tests.test_tournament_history_view::TournamentHistoryViewTest::test_tournament_history_view_lists_all_tournaments -v 2`
Expected: Test fails with "TemplateDoesNotExist: tournament/history.html"

Note: We'll create the template in the next task.

**Step 6: Commit**

```bash
git add tournament/views.py tournament/urls.py tournament/tests/test_tournament_history_view.py
git commit -m "feat: add tournament history list view"
```

---

## Task 8: Create Tournament History Template

**Files:**
- Create: `tournament/templates/tournament/history.html`

**Step 1: Create tournament history template**

```html
<!-- tournament/templates/tournament/history.html -->
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="bg-slate-50 min-h-screen">
    <header class="relative h-32 sm:h-48 md:h-64 w-full bg-cover bg-center"
        style="background-image: url({% static 'img/tennis-background.jpg' %});">
        <div class="absolute inset-0 bg-black opacity-10"></div>
        <div class="relative z-10 flex h-full items-center justify-start px-4">
            <h1 class="font-monofett text-3xl sm:text-3xl md:text-4xl lg:text-7xl text-gray-200 tracking-wider font-thin">
                Tournament History
            </h1>
        </div>
    </header>

    <div class="container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto">
            <div class="bg-white rounded-lg shadow-md overflow-hidden">
                <div class="divide-y divide-gray-200">
                    {% for tournament in tournaments %}
                    <a href="{% url 'tournament_detail' tournament.id %}"
                       class="block hover:bg-gray-50 transition duration-150 ease-in-out">
                        <div class="px-6 py-4">
                            <div class="flex items-center justify-between">
                                <div class="flex-1">
                                    <h3 class="text-lg font-semibold text-gray-900">
                                        {{ tournament.name }}
                                    </h3>
                                    <p class="text-sm text-gray-600 mt-1">
                                        {{ tournament.start_date|date:"F d, Y" }}
                                        {% if tournament.end_date %}
                                            - {{ tournament.end_date|date:"F d, Y" }}
                                        {% endif %}
                                    </p>
                                </div>
                                <div class="ml-4">
                                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
                                        {% if tournament.status == 'ONGOING' %}
                                            bg-green-100 text-green-800
                                        {% else %}
                                            bg-gray-100 text-gray-800
                                        {% endif %}">
                                        {{ tournament.get_status_display }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </a>
                    {% empty %}
                    <div class="px-6 py-8 text-center text-gray-500">
                        No tournaments found.
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="mt-6 text-center">
                <a href="{% url 'tournament_grid' %}"
                   class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Back to Current Tournament
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 2: Run tests to verify they pass**

Run: `python manage.py test tournament.tests.test_tournament_history_view -v 2`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tournament/templates/tournament/history.html
git commit -m "feat: create tournament history template"
```

---

## Task 9: Add Prev/Next Navigation to Grid Template

**Files:**
- Modify: `tournament/templates/tournament/grid.html:1-44`

**Step 1: Add navigation arrows to grid template**

```html
<!-- tournament/templates/tournament/grid.html -->
{% extends "base.html" %}
{% load custom_tags %}

{% block content %}
<div class="bg-slate-50 container mx-auto">
    {% include "components/header.html" with tournament=tournament %}

    <!-- Prev/Next Navigation -->
    <div class="w-full max-w-3xl md:max-w-5xl lg:max-w-6xl mx-auto px-4 pt-4">
        <div class="flex justify-between items-center mb-4">
            <div>
                {% if prev_tournament %}
                <a href="{% url 'tournament_detail' prev_tournament.id %}"
                   class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    <svg class="mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    Previous
                </a>
                {% else %}
                <div class="inline-flex items-center px-4 py-2 border border-gray-200 text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed">
                    <svg class="mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                    Previous
                </div>
                {% endif %}
            </div>

            <a href="{% url 'tournament_history' %}"
               class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                View All Tournaments
            </a>

            <div>
                {% if next_tournament %}
                <a href="{% url 'tournament_detail' next_tournament.id %}"
                   class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Next
                    <svg class="ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                </a>
                {% else %}
                <div class="inline-flex items-center px-4 py-2 border border-gray-200 text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed">
                    Next
                    <svg class="ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <div class="w-full max-w-3xl md:max-w-5xl lg:max-w-6xl mx-auto p-4"
        x-data="{ activeTab: '{{ group_data.0.group.name }}' }">

        <!-- Tab Headers -->
        <div class="bg-gray-200 rounded-t-lg shadow-md overflow-hidden">
            <div class="flex">
                {% for data in group_data %}
                {% with group_index=forloop.counter0 %}
                <button class="flex-1 py-3 px-4 text-center text-base transition duration-200 ease-in-out relative"
                    :class="{
                        'bg-tab-badge-{{ group_index }} text-black font-bold': activeTab === '{{ data.group.name }}',
                        'bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium': activeTab !== '{{ data.group.name }}'
                    }"
                    @click="activeTab = '{{ data.group.name }}'">
                    {{ data.group.name }}
                    <div class="absolute bottom-0 left-0 right-0 h-1 transition-all duration-200 ease-in-out"
                        :class="{'opacity-100 bg-tab-badge-{{ group_index }}': activeTab === '{{ data.group.name }}', 'opacity-0 bg-gray-200': activeTab !== '{{ data.group.name }}'}">
                    </div>
                </button>
                {% endwith%}
                {% endfor %}
            </div>
        </div>

        <!-- Tab Content -->
        <div class="bg-white rounded-b-lg shadow-md p-4" x-show="activeTab"
            x-transition:enter="transition ease-out duration-300"
            x-transition:enter-start="opacity-0 transform scale-95"
            x-transition:enter-end="opacity-100 transform scale-100">
            {% for data in group_data %}
            {% with group_count=forloop.counter0 %}
            {% include "components/group_tab.html" with data=data group=data.group group_index=group_count %}
            {% endwith %}
            {% endfor %}
        </div>
    </div>
</div>
{% endblock %}
```

**Step 2: Update TournamentGridView to include prev/next context**

```python
# tournament/views.py (modify TournamentGridView.get_context_data)
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    # Get latest ongoing tournament
    tournament = (
        Tournament.objects.filter(status="ONGOING", end_date__isnull=True)
        .order_by("-start_date")
        .first()
    )

    if not tournament:
        return context

    # Pass tournament object for header and navigation
    context["tournament"] = tournament

    # Use service to build grid data
    grid_builder = TournamentGridBuilder()
    context["group_data"] = grid_builder.build_grid_data(tournament)

    # Add prev/next tournament IDs for navigation (only if viewing current)
    context["prev_tournament"] = None
    context["next_tournament"] = None

    return context
```

**Step 3: Commit**

```bash
git add tournament/templates/tournament/grid.html tournament/views.py
git commit -m "feat: add prev/next navigation to grid template"
```

---

## Task 10: Update URL Configuration

**Files:**
- Modify: `tennis_doubles/urls.py`

**Step 1: Add tournament app URLs to main URLconf**

```python
# tennis_doubles/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tournament.views import TournamentGridView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TournamentGridView.as_view(), name='tournament_grid'),
    path('', include('tournament.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

**Step 2: Verify URLs work**

Run: `python manage.py show_urls` (if django-extensions installed) or manually test
Expected: All URL patterns registered correctly

**Step 3: Commit**

```bash
git add tennis_doubles/urls.py
git commit -m "feat: update URL configuration for tournament views"
```

---

## Task 11: Update Admin with TournamentGroup Inline

**Files:**
- Modify: `tournament/admin.py:1-17`

**Step 1: Add TournamentGroup inline to Tournament admin**

```python
# tournament/admin.py
from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Tournament, Group, TournamentGroup, Player, Team, Match


class TournamentGroupInline(admin.TabularInline):
    """Inline for managing tournament groups"""
    model = TournamentGroup
    extra = 5  # Show 5 empty forms for adding groups
    max_num = 5  # Maximum 5 groups allowed
    min_num = 2  # Minimum 2 groups required
    validate_min = True
    validate_max = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the group dropdown to show predefined groups"""
        if db_field.name == "group":
            # Only show predefined groups in dropdown
            kwargs["queryset"] = Group.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status']
    list_filter = ['status']
    inlines = [TournamentGroupInline]

    def save_model(self, request, obj, form, change):
        """Validate group count before saving"""
        super().save_model(request, obj, form, change)
        # Validation will be triggered by Tournament.clean() on save


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name']


# TournamentGroup admin removed since it's managed via inline
# @admin.register(TournamentGroup)
# class TournamentGroupAdmin(admin.ModelAdmin):
#     list_display = ['tournament', 'group']
#     list_filter = ['tournament', 'group']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'player1', 'player2', 'get_group', 'get_tournament', 'rank']
    list_filter = ['tournament_group__group', 'tournament_group__tournament']
    search_fields = ['player1__first_name', 'player1__last_name',
                    'player2__first_name', 'player2__last_name']

    def get_group(self, obj):
        return obj.tournament_group.group
    get_group.short_description = 'Group'
    get_group.admin_order_field = 'tournament_group__group'

    def get_tournament(self, obj):
        return obj.tournament_group.tournament
    get_tournament.short_description = 'Tournament'
    get_tournament.admin_order_field = 'tournament_group__tournament'


class MatchAdminForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['tournament', 'team1', 'team2', 'set1_team1', 'set1_team2',
                 'set2_team1', 'set2_team2', 'set3_team1', 'set3_team2',
                 'date_played', 'retired_team']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # For both new instances and edits, get the tournament
        tournament = None
        if self.instance.pk:
            tournament = self.instance.tournament
        elif self.data.get('tournament'):
            try:
                tournament = Tournament.objects.get(pk=self.data.get('tournament'))
            except Tournament.DoesNotExist:
                pass

        # Set the team querysets based on tournament
        if tournament:
            teams = Team.objects.filter(tournament_group__tournament=tournament)
            self.fields['team1'].queryset = teams
            self.fields['team2'].queryset = teams
        else:
            self.fields['team1'].queryset = Team.objects.none()
            self.fields['team2'].queryset = Team.objects.none()


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    form = MatchAdminForm
    list_display = ('__str__', 'tournament', 'date_played', 'get_score', 'retired_team')
    list_filter = ('tournament', 'team1__tournament_group', 'date_played', 'retired_team')

    class Media:
        js = ('js/match_admin.js',)
```

**Step 2: Commit**

```bash
git add tournament/admin.py
git commit -m "feat: add TournamentGroup inline to Tournament admin"
```

---

## Task 12: Rebuild Tailwind CSS

**Files:**
- N/A (build process)

**Step 1: Rebuild CSS with new colors**

Run: `npm run build`
Expected: Tailwind rebuilds CSS including new tab-badge colors

**Step 2: Verify CSS file updated**

Run: `ls -lh tournament/static/css/output.css`
Expected: File timestamp updated, size may have changed

**Step 3: Collect static files for production**

Run: `python manage.py collectstatic --noinput`
Expected: Static files collected including updated CSS

**Step 4: Commit**

```bash
git add tournament/static/css/output.css staticfiles/
git commit -m "build: rebuild Tailwind CSS with new tab colors"
```

---

## Task 13: Manual Testing & Validation

**Testing Checklist:**

**Step 1: Test migration and group creation**
- [ ] Run `python manage.py migrate` - succeeds
- [ ] Check 8 predefined groups exist in admin
- [ ] Verify existing tournaments still work

**Step 2: Test admin validation**
- [ ] Create tournament with 1 group - fails with error
- [ ] Create tournament with 2 groups - succeeds
- [ ] Create tournament with 5 groups - succeeds
- [ ] Create tournament with 6 groups - fails with error

**Step 3: Test UI with multiple group counts**
- [ ] Create tournament with 2 groups - tabs display correctly
- [ ] Create tournament with 3 groups - tabs display correctly with 3 colors
- [ ] Create tournament with 4 groups - tabs display correctly with 4 colors
- [ ] Create tournament with 5 groups - tabs display correctly with 5 colors

**Step 4: Test tournament history**
- [ ] Access `/tournaments/` - shows list of all tournaments
- [ ] Click tournament - navigates to specific tournament grid
- [ ] Verify "View All Tournaments" link works
- [ ] Test prev/next navigation between tournaments
- [ ] Verify arrows disabled at boundaries

**Step 5: Test header**
- [ ] Header displays tournament name (not hardcoded text)
- [ ] Header updates when viewing different tournaments

**Step 6: Run all tests**

Run: `python manage.py test tournament.tests -v 2`
Expected: All tests PASS

**Step 7: Final commit**

```bash
git add .
git commit -m "chore: complete variable groups feature implementation"
```

---

## Completion

All tasks completed. The system now supports:
- 2-5 groups per tournament with validation
- Predefined group names (Racketeers, Serve-ivors, Smashers, Volleyers, Lobbers, Baseliners, Net Rushers, Groundstrokers)
- Tournament history page with full list of tournaments
- Prev/Next navigation between tournaments
- Dynamic header showing tournament names
- Extended tab colors supporting up to 5 groups
- Admin interface with inline group selection and validation

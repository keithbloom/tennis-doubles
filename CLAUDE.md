# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Django 5.1 web application for managing and displaying tennis doubles tournaments. Uses SQLite for local development and is deployed to Fly.io.

## Development Commands

### Setup
```bash
# Python dependencies (activate venv first)
source .venv/bin/activate
pip install -r requirements.txt

# Node (Tailwind CSS only)
npm install
```

### Running Locally
```bash
# In one terminal — watch and rebuild Tailwind CSS
npm run build

# In another terminal
python manage.py runserver
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py restore_db   # Restore from S3 backup (requires AWS env vars)
python manage.py backup_db    # Backup to S3
python manage.py create_tournament [name]  # Creates new tournament copying previous groups/teams
```

### Testing
```bash
python manage.py test                          # All tests
python manage.py test tournament.tests.test_services  # Single test module
python manage.py test tournament.tests.test_services.StandingsCalculatorTest.test_something  # Single test
```

## Environment Variables

Create a `.env` file in the project root:
```
SECRET_KEY=
DEBUG=True
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BACKUP_BUCKET_NAME=
```

## Architecture

### Data Model
The core hierarchy: `Tournament` → `TournamentGroup` (M2M through table) → `Team` → `Player`.

- **Tournament**: Has status (ONGOING/COMPLETED), date range; validated to have 2–5 groups
- **Group**: Predefined named groups (e.g. "Group A"); reused across tournaments via `TournamentGroup`
- **TournamentGroup**: Through table linking a tournament to a group; teams belong to this, not directly to Tournament or Group
- **Team**: Two players in a tournament group, with an optional `rank` and `is_withdrawn` flag
- **Match**: Belongs to a tournament, references two teams (must be in the same tournament group). Stores set scores; supports a `retired_team` field for injury retirements

### Scoring
Points per match: 1 point for playing + 1 per set won + 1 bonus for match winner (max 4 points). Retirement matches: winner gets 4 points, loser gets 1.

### Service Layer (`tournament/services.py`)
Business logic is separated into services:
- `MatchResultService` — calculates results, sets won, points, and games for a single match
- `StandingsCalculator` — aggregates team statistics across all matches in a group and sorts by points → set % → game %
- `TournamentGridBuilder` — builds the full grid data structure (teams × teams matrix) consumed by the grid template

### Views (`tournament/views.py`)
- `TournamentGridView` — shows the current ONGOING tournament (no end date, start date ≤ today)
- `TournamentDetailView` — shows a specific tournament by ID with prev/next navigation
- `TournamentHistoryView` — lists all tournaments
- `teams_by_tournament`, `previous_partner` — staff-only JSON API endpoints used by admin JS

### Admin (`tournament/admin.py`)
All data is managed via the Django admin. `MatchAdmin` and `TeamAdmin` load custom JS (`match_admin.js`, `team_admin.js`) that make AJAX calls to the JSON API endpoints to filter teams by tournament and auto-populate previous partners.

### Templates
- `tournament/templates/tournament/grid.html` — main tournament view
- `tournament/templates/components/` — reusable components (match grid, standings, header, tabs)
- Custom template tags in `tournament/templatetags/custom_tags.py`: `team_name`, `header`, `section_tabs` (render component templates), plus `get_item` filter and `sub` filter

### CSS
Tailwind CSS is compiled from `tournament/static/css/tailwind.css` → `tournament/static/css/output.css`. Run `npm run build` to watch and recompile. There is also `custom_fonts.css` for the Cowboys webfont.

### Deployment
Deployed to Fly.io via GitHub Actions (`.github/workflows/fly-deploy.yml`). Static files are served by WhiteNoise.

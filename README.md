# Tennis Doubles Tournament Manager

This Django web application helps manage and display tennis doubles tournaments. It provides a user-friendly interface for organizing matches, tracking scores, and viewing tournament grids.

## Features

- Tournament group management
- Match scheduling and score tracking
- Responsive tournament grid display
- Admin interface for easy data management

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- npm (Node.js package manager) for tailwind css

## Setup and installation

This require python and node to be installed. Use pyenv and fnm to manage the runtime versions, the repo contains versions file that these managers will respect.

### Start the node build to generate the Tailwind CSS

Node is only used for generating the Tailwind CSS files. This can be sitting and running in a terminal while developing

```bash
npm install
npm run build
```

### Starting the Django application

Create a virtual environment and install dependencies:
```
python -m venv venv 
source venv/bin/activate # On Windows, use venv\Scripts\activate
pip install -r requirements.txt
```

Create a local .env file from this template (if this is missing you will get runtime errors)

```bash
SECRET_KEY=
DEBUG=True
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BACKUP_BUCKET_NAME=
```

Setup the Django site:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Restore a current backup of the live database:

```bash
python manage.py restore_db
python manage.py migrate
```

Run the application

```bash
python manage.py runserver
```

## Management commands
These are custom management commands added to `./management/commands/`

#### Backup and restore the database 

These commands use and S3 bucket to store and retrieve the database backup from. The keys for S3 must be present in the ENV

To backup the database run:

```bash
python manage.py backup_db 
```

To restore the database run:

```bash
python manage.py backup_db 
```
#### Create tournament

Running `python manage.py create_tournament [tournament_name]` where will create a new tournament using the supplied name. It will populate the groups and the teams using the previous tournament with the most recent start_date.

# KanMind

KanMind is a Kanban board application built with Django REST Framework backend and JavaScript frontend. It allows users to create boards, add tasks, and manage their workflow effectively.

## Features

- User authentication and authorization
- Create and manage Kanban boards
- Add and organize tasks in columns
- Assign tasks to users
- Add reviewers to tasks
- Comment on tasks
- Role-based permissions (Admin, Editor, Viewer)

## Technology Stack

- **Backend**: Django 5.2.3, Django REST Framework 3.16.0
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Token-based authentication

## Prerequisites

- Python 3.8+
- Git
- Web browser

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd KanMind
```

### 2. Set up virtual environment

```bash
python -m venv env
```

#### On Windows:
```bash
env\Scripts\activate
```

#### On macOS/Linux:
```bash
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Database setup

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. (Optional) Load sample data

```bash
python manage.py loaddata fixtures/sample_data.json
```

## Running the Project

### Start the backend server

```bash
python manage.py runserver
```

The server will start at http://127.0.0.1:8000/

### Access the application

- **API**: http://127.0.0.1:8000/api/
- **Admin Interface**: http://127.0.0.1:8000/admin/
- **Frontend**: Open your frontend files in a local development server

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/auth/` | Authentication endpoints |
| `/api/boards/` | Board and column management |
| `/api/tasks/` | Task and comment management |

## Development

### Code Quality

```bash
# Format code
black .

# Lint code  
flake8 .

# Run tests
pytest
```

### Database Operations

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Production Deployment

1. Set `DEBUG=False` in your environment
2. Configure proper database (PostgreSQL recommended)
3. Set up proper CORS settings
4. Use environment variables for sensitive data
5. Configure static file serving

## Troubleshooting

### Common Issues

1. **Migration errors**: Run `python manage.py migrate --fake-initial`
2. **Permission errors**: Ensure proper file permissions on database
3. **CORS errors**: Check CORS settings in `settings.py`

### Support

For issues and questions, please check the documentation or create an issue in the repository.


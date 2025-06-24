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
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Token-based authentication

## Dependencies

The project requires the following packages:
- asgiref==3.8.1
- Django==5.2.3
- django-cors-headers==4.7.0
- djangorestframework==3.16.0
- sqlparse==0.5.3
- tzdata==2025.2

All dependencies are listed in the requirements.txt file.

## Project Structure

- `auth_app/`: Authentication and user management
- `kanban_app/`: Board and column management
- `tasks_app/`: Task and comment management
- `core/`: Project settings and main URL configuration

## Prerequisites

- Python 3.8+
- Git
- Web browser

## Installation

### Clone the repository

```bash
git clone <repository-url>
cd KanMind
```

### Set up virtual environment

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

### Install dependencies

```bash
pip install -r requirements.txt
```

### Database setup

```bash
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

## Running the Project

### Start the backend server

```bash
python manage.py runserver
```

The server will start at http://127.0.0.1:8000/

### Access the frontend

Open `KanMind_Frontend/project.KanMind/index.html` in your web browser or use a local development server.

## API Endpoints

- Authentication: `/api/auth/`
- Kanban boards and columns: `/api/kanban/`
- Tasks and comments: `/api/tasks/`

## API Documentation

You can explore the API by navigating to the endpoints in your browser after running the server.

## Admin Interface

Access the admin interface at http://127.0.0.1:8000/admin/ using your superuser credentials.

## Development

### Making Changes

After making changes, you can use the provided `up.bat` script to commit and push your changes:

```bash
up.bat "Your commit message here"
```

This will pull the latest changes, add your changes, commit with your message, and push to the repository.

## CORS Configuration

The application allows CORS from the following origins:
- http://localhost:5500
- http://127.0.0.1:5500

If you need to add more origins, modify the `CORS_ALLOWED_ORIGINS` setting in `core/settings.py`.
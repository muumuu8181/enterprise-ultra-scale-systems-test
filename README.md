# Court Case Management System

A prototype Django application for managing court cases, hearings, and parties.

## Requirements

*   Python 3.12+
*   Django 6.0.2+

## Setup

1.  **Clone the repository** (if applicable)

2.  **Install dependencies**:
    ```bash
    pip install django
    ```

3.  **Apply Migrations**:
    Navigate to the project directory:
    ```bash
    cd court_system
    python manage.py migrate
    ```

4.  **Create Superuser (Optional)**:
    ```bash
    python manage.py createsuperuser
    ```

## Running the Server

Start the development server:

```bash
cd court_system
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000/cases/`.

## Running Tests

To run the unit tests:

```bash
cd court_system
python manage.py test cases
```

## Features

*   **Case Management**: Create and view legal cases.
*   **Automatic Case Numbering**: Cases are automatically assigned a unique number (e.g., `2024-CIV-0001`).
*   **Parties**: Track plaintiffs, defendants, and lawyers associated with cases.
*   **Hearings**: Schedule court hearings.
*   **Documents**: Manage case-related documents.

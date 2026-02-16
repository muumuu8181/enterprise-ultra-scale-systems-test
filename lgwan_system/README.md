# LGWAN Integrated Administrative System

This is a prototype of an Integrated Administrative System for Local Governments, built with Django.

## Project Structure

The project is organized into the following applications:

*   **`common`**: Core utilities and shared components. Includes `AuditLog` for tracking data access.
*   **`residents`** (Jumin Kiroku): Manages Resident Records (Basic Resident Register).
    *   Models: `Household`, `Resident`
    *   Features: Move-in (Tennyu), Move-out (Tenshutsu), Certificate Issuance (Juminhyo).
*   **`tax`** (Taxation): Manages Resident Tax calculations.
    *   Models: `TaxPayer`, `TaxAssessment`
    *   Features: Basic tax calculation based on income.
*   **`welfare`** (Welfare): Manages Welfare information.
    *   Models: `WelfareRecipient`, `AssistanceRecord`
    *   Features: Record keeping for welfare assistance.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd lgwan_system
    ```

2.  **Install dependencies:**
    ```bash
    pip install django
    ```

3.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```

4.  **Run the server:**
    ```bash
    python manage.py runserver
    ```

## API Endpoints (Residents)

### Move-in Registration
*   **URL:** `/residents/move-in/`
*   **Method:** `POST`
*   **Body:**
    ```json
    {
        "address": "1-2-3 Chiyoda, Tokyo",
        "residents": [
            {
                "name_kanji": "Test Taro",
                "name_kana": "Test Taro",
                "dob": "1990-01-01",
                "gender": "M",
                "my_number": "123456789012"
            }
        ]
    }
    ```

### Move-out Registration
*   **URL:** `/residents/move-out/`
*   **Method:** `POST`
*   **Body:**
    ```json
    {
        "resident_id": 1,
        "move_out_date": "2023-10-27"
    }
    ```

### Certificate Issuance
*   **URL:** `/residents/certificate/<resident_id>/`
*   **Method:** `GET`

## Testing

Run the test suite using:
```bash
python manage.py test
```

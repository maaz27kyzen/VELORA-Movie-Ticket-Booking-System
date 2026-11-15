# VELORA – Movie Ticket Booking System

**Where Every Frame Becomes an Experience.**

VELORA is a web-based movie ticket booking system developed using Django and MySQL. It provides an elegant cinema-booking experience where users can explore movies, browse theatres and showtimes, select seats, and confirm reservations.

## Features

- Browse currently available movies.
- View movie details and screening information.
- Explore theatres and available showtimes.
- Interactive seat selection.
- Real-time seat availability.
- Guest checkout and booking confirmation.
- Automatic booking reference generation.
- Prevention of duplicate seat bookings using database transactions.
- Django administration panel for managing cinema records.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Database | MySQL |
| Database Connectivity | MySQL Client |
| Development Environment | Visual Studio Code |
| Version Control | Git and GitHub |

## Database Design

The project uses a relational MySQL database consisting of nine main tables:

1. Customer
2. Movie
3. Theatre
4. Screen
5. Seat
6. Movie_Show
7. Show_Seat
8. Booking
9. Booking_Seat

The database manages customer information, movie schedules, theatre details, seat availability, and booking records.

## Project Structure

```text
moviedbproject/
│
├── booking/
│   ├── migrations/
│   ├── static/
│   │   └── booking/
│   │       ├── css/
│   │       └── images/
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── movie_detail.html
│   │   ├── seat_selection.html
│   │   ├── booking_checkout.html
│   │   └── booking_success.html
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
│
├── movies_booking/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── .env
├── .gitignore
├── manage.py
└── requirements.txt
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/maaz27kyzen/VELORA-Movie-Ticket-Booking-System.git
cd VELORA-Movie-Ticket-Booking-System
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root directory.

Add the following configuration using your own MySQL credentials:

```env
DJANGO_SECRET_KEY=your_secret_key
DB_NAME=movie_booking_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Never upload your `.env` file or expose your database credentials.

### 5. Set up the MySQL database

Create the MySQL database and configure the nine required tables according to the project's database schema.

The project uses manually created MySQL tables, so the database must be prepared before running the application.

### 6. Run the Django development server

```bash
python manage.py runserver
```

Open the application at:

http://127.0.0.1:8000/

## Administration

The Django administration panel can be accessed at:

http://127.0.0.1:8000/admin/

## Project Purpose

This project was developed as an academic DBMS project to demonstrate relational database design, Django–MySQL integration, CRUD operations, database transactions, and a practical movie ticket reservation workflow.

## Future Enhancements

- Online payment gateway integration.
- Email-based booking confirmations.
- User registration and login.
- QR-code-based digital tickets.
- Advanced movie filtering and search.

---

**Developed as an academic project.**

**Project:** VELORA – Movie Ticket Booking System
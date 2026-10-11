# Beauty Parlour Management and Feedback System

A full-stack web application designed for beauty salons to present their services, engage with clients, collect customer reviews, and analyze customer satisfaction metrics.

---

## 1. Project Overview

The **Beauty Parlour Management System** serves as a digital touchpoint for salon operations. It bridges the gap between client experience and administrative oversight by providing:
- An interactive catalog of parlour services with descriptions and transparent pricing.
- A client review and rating module to collect authentic customer feedback.
- A secure administrative dashboard for catalog management and rating analytics.
- Cloud database integration for persistent and scalable data storage.

---

## 2. System Architecture & Features

### Client-Facing Portal
- **Service Catalog**: Displays all available treatments categorized with descriptions and real-time rates.
- **Client Feedback**: Allows visitors to rate individual services on a 1-to-5 star scale and submit written testimonials.
- **Testimonial Showcase**: Highlights recent verified customer reviews dynamically loaded from the database.
- **Business Details**: Presents working hours, location details, and direct contact information.

### Administrative Management Portal
- **Secure Authentication**: Protected admin login with hashed password verification.
- **Service Management**: Real-time CRUD (Create, Read, Update, Delete) operations for service offerings and prices.
- **Rating Analytics**:
  - Total feedback volume and overall customer satisfaction score.
  - Service-specific performance breakdown and review count.
  - Rating distribution metrics (1 to 5 star frequency).
  - Identification of highest and lowest-rated services.

---

## 3. Technology Stack

- **Backend**: Python 3.12+, Flask
- **Database**: MongoDB Atlas (NoSQL)
- **Database Driver**: PyMongo
- **Security**: Werkzeug (`generate_password_hash`, `check_password_hash`), session cookies
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Web Server (Production)**: Gunicorn

---

## 4. Database Schema

The system utilizes MongoDB collections within the `purvi_beauty_parlour` database:

### `services` Collection
```json
{
  "name": "Facials & Skincare",
  "description": "Personalised skincare and facial treatments.",
  "price": 699.0
}
```

### `feedback` Collection
```json
{
  "name": "Priya Sharma",
  "service": "Facials & Skincare",
  "rating": 5,
  "message": "Wonderful experience, highly recommended!",
  "created_at": "2026-10-11T12:00:00+00:00"
}
```

### `admin_settings` Collection
```json
{
  "_id": "main_admin",
  "username": "admin",
  "password_hash": "scrypt:32768:8:1$..."
}
```

---

## 5. Local Setup and Execution

### Prerequisites
- Python 3.10 or higher
- MongoDB Atlas cluster account (or local MongoDB server)

### Installation Steps

1. **Clone or open the project folder in your terminal:**
   ```bash
   cd purvi_beauty_parlour_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows:
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database Connection:**
   Open `config.py` and set your MongoDB Atlas connection URI:
   ```python
   MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the application:**
   - Main Website: `http://127.0.0.1:5000`
   - Admin Login: `http://127.0.0.1:5000/admin/login`
   - System Health Status: `http://127.0.0.1:5000/health`

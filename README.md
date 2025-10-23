# Dish Oracle 🍽️

A Django-based web app to organize and rate grocery products by personal taste tags, offering personalized recommendations based on your flavor profile.

---

## 🚀 Getting Started

Follow these steps to get a local development copy up and running.  
See **Deployment** for running in production.

---

## 🧰 Prerequisites

You’ll need:

- Python 3.11+
- pip
- Git
- Virtualenv *(optional but recommended)*
- Docker + Docker Compose
- PostgreSQL (used in Docker by default)

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/dish-oracle.git
cd dish-oracle
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your environment file
```bash
cp env.example .env
```
Then open `.env` and set your own `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, etc.

### 5. Setup and run Docker
```bash
docker-compose up -d
```
This will start a **PostgreSQL** container configured via your `.env`.

### 6. Apply migrations and run server
```bash
python manage.py migrate
python manage.py runserver
```

The app should now be available at:  
👉 http://127.0.0.1:8000

---

## 🧩 Using the App

You can now:

- Add a product via its **13-digit EAN barcode**
- Rate it with **custom tags** (e.g. *Sweet, Spicy, Plastic, Would eat again*)
- Re-rate existing products
- Filter products by **tags** or search by **name**, **company**, **category**

---

## 🧪 Running Tests

To run the full test suite:
```bash
pytest
```

Or to run tests for a specific app:
```bash
pytest [app_name]
```

---

## 🌍 Deployment

To run this on a live server:

- Use **PostgreSQL** instead of SQLite  
- Set `DEBUG=False` in `.env`  
- Set valid `ALLOWED_HOSTS`  
- Run Django with **Gunicorn** or **uWSGI** behind **Nginx**  
- Configure static files with `collectstatic`

*(More deployment notes coming soon.)*

---

## 🧱 Built With

- [Django](https://www.djangoproject.com/)
- [django-environ](https://github.com/joke2k/django-environ)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)

---

## 🤝 Contributing

Pull requests are welcome!  
For major changes, open an issue first to discuss what you’d like to modify.

---

## 🔖 Versioning

This project follows [SemVer](https://semver.org/).  
Current release: `v0.1.0`

---

## 👤 Authors

- [@Mark-s0l](https://github.com/Mark-s0l) — initial design, backend, and project idea.  
See also the list of [contributors](https://github.com/Mark-s0l/dish-oracle/graphs/contributors).

---

## 💬 Acknowledgments

Inspired by frustration at the grocery store 😅

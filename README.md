# Dish Oracle 🍽️

A Django-based web application for rating and organizing grocery products by personal taste tags.

---

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

See **Deployment** for notes on how to run the project in production.

---

## Prerequisites

To run this project, you need:

- Python 3.11+
- pip
- Git
- Virtualenv (optional but recommended)

---

## Installing

Follow these steps to set up a local development environment:

### 1. Clone the repository

git clone https://github.com/yourusername/dish-oracle.git
cd dish-oracle

### 2. Create a virtual environment and activate it

python -m venv venv
source venv/bin/activate # on Linux/macOS
venv\Scripts\activate # on Windows

### 3. Install dependencies

pip install -r requirements.txt

### 4. Create your environment file

cp env.example .env

Then, edit `.env` and set your own `SECRET_KEY`.

### 5. Run development server

python manage.py runserver

---

## Using the App

You can now:

- Add a product via its 13-digit EAN barcode
- Rate it using personal taste tags (e.g. Sweet, Spicy, Plastic, Would eat again)
- Re-rate existing products
- Filter products by tags
- Search by barcode

---

## Running the Tests

TBD — unit tests will be added in future versions.

---

## Deployment

To run this on a live server:

- Replace SQLite with PostgreSQL
- Set `DEBUG=False` in `.env`
- Set `ALLOWED_HOSTS`
- Run with Gunicorn or uWSGI and a reverse proxy like Nginx

More deployment details will be added soon.

---

## Built With

- [Django](https://www.djangoproject.com/) - Web framework
- [django-environ](https://github.com/joke2k/django-environ) - Environment configuration
- SQLite - Default database for development

---

## Contributing

Pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

---

## Versioning

This project uses [SemVer](https://semver.org/) for versioning.  
Initial release is tagged as `v0.1.0`.

---

## Authors

- @Mark-s0l – initial design, backend, and project idea.

See also the list of [contributors](https://github.com/Mark-s0l/dish-oracle/graphs/contributors) who participated in this project.

---

## License

This project is licensed under the MIT License – see the [LICENSE.md](LICENSE.md) file for details.

---

## Acknowledgments

Inspired by frustration at the grocery store 😅
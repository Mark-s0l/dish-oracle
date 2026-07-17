# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Recommendation system based on user ratings and tags.

## [1.0.0] - 2026-07-17

### Added
- Add a product via its 13-digit EAN barcode, either manually or by scanning with the camera.
- Rate and re-rate products using a 5-star rating system.
- Tag products with custom taste tags (e.g. Sweet, Spicy, Plastic, Would eat again).
- Search products by name and/or tags, with the ability to combine both in a single query.
- User registration and login.
- Change account email and password, with email confirmation required for password changes.
- Async email delivery via Celery and Redis.
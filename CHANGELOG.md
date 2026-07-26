# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Planned
- Recommendation system based on user ratings and tags.

## [Unreleased]

## [1.2.0] - 2026-07-26

### Changed
- Minimum supported Python version raised to 3.12 (previously 3.11).
- Django upgraded to 6.0 (previously 5.2).

## [1.1.0] - 2026-07-22

### Added
- Search results now display the current user's own rating for each product.

### Fixed
- Product search no longer returns products the current user has not rated themselves, even if another user's rating matches the search query or tag filter.

### Changed
- Tag selector in search now only shows taste tags the current user has applied in their own ratings, instead of all tags in the system.

## [1.0.0] - 2026-07-17

### Added
- Add a product via its 13-digit EAN barcode, either manually or by scanning with the camera.
- Rate and re-rate products using a 5-star rating system.
- Tag products with custom taste tags (e.g. Sweet, Spicy, Plastic, Would eat again).
- Search products by name and/or tags, with the ability to combine both in a single query.
- User registration and login.
- Change account email and password, with email confirmation required for password changes.
- Async email delivery via Celery and Redis.

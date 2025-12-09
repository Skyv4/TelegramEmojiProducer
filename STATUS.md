# Project Status

## Frontend (app/)

### Feature: User Upload (Files & URLs)
- [ ] Allow users to upload emoji files for conversion.
- [ ] Allow users to upload links (URLs) to emojis for conversion.
- [ ] Display conversion results for individual files/URLs.

### Feature: Admin Page
- [ ] Create a new Next.js page for admin functionalities (e.g., `/admin`).
- [ ] Implement basic authentication for the admin page.
- [ ] Display a list of all conversion requests.
- [ ] Add functionality to mark requests as completed.
- [ ] Automatically convert and display WebM alongside the original file/link for review.

## Backend (backend/)

### Feature: URL Conversion
- [x] Add `requests` library to `requirements.txt` and `pyproject.toml`.
- [x] Implement a new API endpoint `/api/convert-url` to handle URL submissions.
- [x] Download the file from the provided URL.
- [x] Validate the downloaded file type (GIF/video).
- [x] Process the downloaded file using `convert_to_telegram_sticker`.

### Feature: Admin Endpoints & Database
- [x] Create a `db.json` file for storing conversion request metadata.
- [x] Create `database.py` with functions to:
    - [x] Load and save conversion requests from/to `db.json`.
    - [x] Add new conversion requests.
    - [x] Get all conversion requests.
    - [x] Update conversion request status.
    - [x] Get a single conversion request by ID.
- [x] Integrate database functions into `/api/convert` and `/api/convert-url` to log requests.
- [x] Implement basic authentication for admin endpoints.
- [x] Create `/api/admin/requests` to retrieve all conversion requests.
- [x] Create `/api/admin/requests/{request_id}/complete` to mark a request as completed.
- [x] Create `/api/admin/requests/{request_id}` to retrieve a single request.


# Software Requirements Specification (SRS): Personal Media Tracker

## 1. Introduction
### 1.1 Purpose
This document outlines the software requirements for a custom, web-based personal media tracking application. The system will allow the user to catalog, search, and track their viewing history for movies and television series, serving as a customized alternative to third-party platforms like Trakt.tv.

### 1.2 Scope
The application is initially designed for single-user, personal use but will be architected with multi-tenant abstractions to support future public scaling. It will utilize The Movie Database (TMDB) API for all metadata and image retrieval. TV tracking is strictly limited to standard numbered seasons and episodes.

## 2. Overall Description
### 2.1 User Characteristics
The primary user requires a streamlined, data-rich interface free of unnecessary social features or cluttered UI updates. The user has administrative access to a Linux Virtual Private Server (VPS) for deployment.

### 2.2 Operating Environment
* **Deployment:** Linux VPS.
* **Containerization:** Docker (for isolated application environments).
* **Web Server:** Nginx (acting as a reverse proxy and serving static frontend assets).
* **Client:** Modern desktop and mobile web browsers.

## 3. Functional Requirements
### 3.1 Media Discovery & Addition
* **Search:** The system must allow the user to search for movies and TV shows via the TMDB API.
* **Add to Library:** The user must be able to add a selected movie or TV show to their local database, which triggers a background fetch of relevant metadata (title, overview, release date, poster path) and episode lists (for series).

### 3.2 Watch Tracking
* **Manual Entry:** The user must be able to manually mark a movie or a specific TV episode as "watched."
* **Timestamping:** Every "watched" action must record the exact date and time of the event in a historical ledger.

### 3.3 Dashboard Views
* **In-Progress Series:** A dedicated view displaying TV shows where the user has watched at least one episode but has not completed all available episodes. It must calculate and display the number of remaining episodes.
* **Watch History:** A chronological feed displaying the user's most recently watched movies and episodes.

### 3.4 Statistics & Analytics
The system must calculate and display real-time statistics based on the user's watch history, including:
* Total number of movies watched.
* Total number of TV episodes watched.
* Total duration (hours/days) spent watching movies.
* Total duration spent watching TV series.
* Number of currently "In Progress" series.
* Total remaining hours of unwatched episodes in the "In Progress" queue.

### 3.5 Data Migration
* **Trakt.tv Import:** The system must include a one-time execution script to parse a Trakt.tv data export (CSV/JSON), map the entries to TMDB IDs, fetch the metadata, and populate the local database.

### 3.6 Automated Syncing
* **TMDB Updates:** The system must run a scheduled task to check TMDB for newly aired seasons and episodes for TV shows currently marked as "Returning Series" in the local database.

## 4. Non-Functional Requirements
### 4.1 Performance & Resource Efficiency
* The application must have a minimal memory footprint, suitable for deployment on a budget-friendly Linux VPS alongside other applications.
* Images and posters must be served directly via TMDB's Content Delivery Network (CDN) to minimize local bandwidth and storage consumption.

### 4.2 Scalability & Extensibility
* **Multi-tenant Design:** All data interactions must be tied to a specific `user_id` to allow future onboarding of multiple users.
* **Database Abstraction:** The Object-Relational Mapping (ORM) layer must allow seamless transitioning from a local file-based database to a robust relational database engine without altering business logic.

## 5. Technology Stack
To meet the requirements for lightweight performance and rapid API development, the following stack will be utilized:

* **Frontend Application:** Vue.js (Single Page Application)
* **Frontend Styling:** Tailwind CSS
* **Backend Framework:** Python with FastAPI
* **Database:** SQLite (Local, file-based)
* **ORM:** SQLAlchemy (Provides the abstraction layer for future PostgreSQL migration)
* **External API:** The Movie Database (TMDB) API v3/v4
* **Infrastructure:** Linux VPS, Nginx, Docker, Cron (for scheduled background tasks)

## 6. System Architecture Summary
1.  **Nginx** listens on ports 80/443, handles SSL, and serves the static compiled **Vue.js** frontend.
2.  API requests from the frontend are routed by Nginx to the **FastAPI** backend running inside a **Docker** container.
3.  **FastAPI** queries the **SQLite** database via **SQLAlchemy** to construct user dashboards.
4.  A system-level **cron job** triggers a protected backend endpoint twice a week to synchronize returning TV show data with **TMDB**.
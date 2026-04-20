# Software Requirements Specification (SRS): CineTrack

## 1. Introduction
### 1.1 Purpose
This document outlines the software requirements for CineTrack, a custom, web-based personal media tracking application. The system allows users to catalog, search, and track their viewing history for movies and television series, serving as a lightweight, self-hosted alternative to platforms like Trakt.tv.

### 1.2 Scope
CineTrack is designed for personal use with a focus on data privacy and minimal resource consumption. It utilizes The Movie Database (TMDB) API for metadata and image retrieval.

## 2. Overall Description
### 2.1 User Characteristics
The primary user requires a streamlined, data-rich interface free of social features or cluttered UI. The user has administrative access to a Linux environment for deployment.

### 2.2 Operating Environment
* **Deployment:** Docker-compatible environment (VPS, Home Server, etc.).
* **Containerization:** Unified Docker image containing both frontend and backend.
* **Web Server:** Internal Nginx (proxying to FastAPI and serving static assets).
* **Client:** Modern web browsers.

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
1.  **Unified Docker Container:** A single image contains both the **Nginx** web server and the **FastAPI** backend.
2.  **Internal Nginx:** Serves the static **Vue.js** frontend and proxies `/api` requests to the local backend process.
3.  **FastAPI Backend:** Handles business logic, TMDB integration, and database operations.
4.  **SQLite Database:** Persistent storage for user data and watch history, stored in a Docker volume.
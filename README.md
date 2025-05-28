# 3GPP Documentation API

This FastAPI service provides an API for managing and serving data extracted from 3GPP documentation. The API is designed to work in tandem with another repository that processes 3GPP documentation, extracts critical information, and generates a finite state machine representation known as a Finite Graph Procedure (FGP).

## Project Overview

The API functions as the backend service responsible for:

- **Data Management:** Handling procedural data and graph representations extracted from 3GPP documentation.
- **Versioning:** Managing multiple versions of state machine graphs for different entities.
- **Data Serving:** Providing endpoints to retrieve, update (insert new versions), and delete graph data.
- **Integration:** Maintaining document references and related content extracted from the documentation processing stage.

## API Documentation

All API endpoints are prefixed with **/procedures**.

### Fetch Operations

#### Get Procedures List

```http
GET /procedures
```

Returns a list of all procedures grouped by document. The response includes:

- Document specifications, versions, and releases.
- Corresponding procedure names.
- Associated entities available for each procedure.

#### Get Latest Graph

```http
GET /procedures/{procedure_id}/{entity}
```

Retrieves the latest version of a graph for a specific procedure and entity. The response includes:

- The graph data (JSON format).
- Metadata such as model name, accuracy, version, and extraction method.
- Document references and a context markdown generated from document sections.
- Timestamps and commit information.

#### Get Version History

```http
GET /procedures/{procedure_id}/{entity}/history
```

Provides the complete version history for a graph associated with a specific procedure and entity.

#### Get Specific Version

```http
GET /procedures/{procedure_id}/{entity}/history/{graph_id}
```

Retrieves a specific version of a graph based on its unique graph ID.

### Insert Operations

#### Update Graph

```http
POST /procedures/{procedure_id}/{entity}
```

Inserts a new version of an edited graph. Key features:

- **Automatic Version Increment:** Determines the next version number automatically.
- **Commit Support:** Accepts commit messages and titles for version tracking.
- **Status Tracking:** Marks the new version with a status (e.g., verified).
- **Metadata Preservation:** Reuses essential metadata such as model name, accuracy, and extraction method from the previous version.

### Delete Operations

#### Delete Graph

```http
DELETE /procedures/{procedure_id}/{entity}
```

Deletes all graphs for a specific procedure and entity combination. The endpoint:

- Removes all versions of a specified graph.
- Automatically deletes the procedure if no graph versions remain.
- Returns a confirmation message detailing the number of deleted items and whether the procedure was also removed.

## Installation Guide

### Prerequisites

- PostgreSQL database (version 17 or higher)
- **uv:** A fast Python package manager and project tool written in Rust. For complete details, refer to the [official uv documentation](https://docs.astral.sh/uv/).

### Setup

1. **Clone the Repository**

   ```bash
   git clone <repository_url>
   cd 3gpp_app/fastapi
   ```

2. **Install uv (if not already installed)**
   The recommended method is to install uv using pipx:

   ```bash
   pipx install uv
   ```

   Alternatively, you may install uv using other methods as described in the official uv docs.

3. **Synchronize Dependencies**
   Use uv to synchronize all required dependencies:

   ```bash
   uv sync
   ```

4. **Configure the Environment**

   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Update the `.env` file with your PostgreSQL credentials and other configuration settings.

5. **Run the Application**
   Start the FastAPI server using uv:
   ```bash
   uv run
   ```
   The application should now be running. Visit `http://localhost:8000/docs` to access the interactive Swagger API documentation.

## Technical Details

- **Framework:** FastAPI
- **Database:** PostgreSQL (using asynchronous connection with psycopg)
- **Data Formats:**
  - UUID for resource identification.
  - JSON for storing graph data.
  - Markdown for storing context references from document sections.
- **State Management:** Each graph record retains:
  - Version history and tracking.
  - Associated entity details (e.g., UE, AMF).
  - Extraction metadata (model, accuracy, extraction method).
  - Commit messages and statuses.
  - Timestamps for creation and updates.

## Dependencies

- FastAPI
- psycopg
- Pydantic (for data validation and serialization)
- Additional libraries for handling database connections and asynchronous operations.

This README provides an overview of the project's structure and key functionalities, serving as a guide for developers and integrators to understand, install, and use the API effectively.

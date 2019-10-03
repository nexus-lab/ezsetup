## Introduction

<!-- TODO: Describe what is ezsetup. Better have a logo. -->

## Installation

### From Source

1. Install dependencies:
    - Python == 3.6
    - Node >= 8.0
    - GNU make
    - PostgreSQL >= 9.6
    - Redis >= 3.2
    - pipenv

2. Copy `.env.example` file to `.env` and fill in necessary fields, and load environment variables by:

    ```bash
    export $(cat .env | xargs)
    ```
    The `API_SERVER` here points to the public address of the EZSetup API service with port number, e.g., `http://127.0.0.1:5002`

3. Initialize database using migration files under `api/database/migrations`

    ```bash
    sudo su postgres -c "psql -c \"CREATE ROLE ${POSTGRES_USER} WITH SUPERUSER CREATEDB CREATEROLE LOGIN ENCRYPTED PASSWORD '${POSTGRES_PASSWORD}';\""
    sudo su postgres -c "createdb ${POSTGRES_USER}"
    sudo su postgres -c "cat api/database/migrations/*.sql | psql -d ${POSTGRES_USER}"
    ```

4. Install requirements for the `frontend` and `api` projects

    ```bash
    make install
    ```

5. Start a redis-queue worker, the API service, and the frontend service using

    ```bash
    make run-worker
    make run-api
    make run-frontend
    ```

## With Docker

1. Install Docker and docker-compose;
2. Copy `.env.example` file to `.env` and fill in necessary fields as described in step 2 of the [source code installation](#from-source).
3. Run `docker-compose up` from your project directory to bring up services.
4. To update the containers to have the lastest EZSetup source code, stop the containers using `docker-compose down`, 
and then rebuild and restart the containers using `docker-compose up --force-recreate --build`

## Contributing

### Coding Styles
<!-- TODO: Use linter to enforce code styles -->
- **HTML & CSS**: [Code Guide by @mdo](http://codeguide.co)
- **JavaScript**: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **Python**: [PEP 8](https://www.python.org/dev/peps/pep-0008/)

### Developing and Deploying
- **API Style**: [GitHub API v3](https://developer.github.com/v3/)
- **Git Commit Style**: [AngularJS Git Commit Message Conventions](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)
- **Veriosning**: [Semantic Versioning 2.0.0](https://semver.org/)

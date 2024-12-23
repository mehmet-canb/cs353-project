# Pool Management System

## Environment Setup

You need to create a `.env` file in the root directory. You can use the `.env.example` file as a reference.

## Local Development

Before running the application, you need to install the dependencies.

```bash
make install-rye
make install-pre-commit
# Alternatively, you can use the following command to install the dependencies:
make install
```

After installing the dependencies, you need to setup the database. You can do so like below:

```bash
make db-init
```

Finally, you can run the application using the following command:

```bash
make local-run
```

## Docker Development

To build the Docker image, you can use the following command:

```bash
make docker-build
```

To run the application using Docker, you can use the following command:

```bash
make docker-run
```

To stop the Docker container, you can use the following command:

```bash
make docker-down
```

To clean up the Docker environment, you can use the following command:

```bash
make docker-clean
```

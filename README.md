# Pool Management System

This repository contains a project designed and implemented as part of our database systems course. The goal of the project was to create a web application that relies solely on raw SQL statements, using a DBMS as the data source.

## Environment Setup

You need to create a `.env` file in the root directory. You can use the `.env.example` file as a reference.

## Local Development

> [!NOTE]
> The instructions below assume that your operating system is **Ubuntu 22.04.5 LTS**. You may need to adjust some of the commands and the makefile contents to properly set up your development environment, depending on your operating system.

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

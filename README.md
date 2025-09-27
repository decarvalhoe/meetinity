# Meetinity Project

**Meetinity** is a professional networking platform designed to help users connect, discover events, and grow their professional network. This repository serves as the main entry point for the project, providing a comprehensive overview of the architecture and the different services that compose the platform.

## Project Overview

The Meetinity platform is built on a microservices architecture, with a React-based mobile application and an administration portal. The project is divided into seven main repositories, each responsible for a specific part of the platform.

### Architecture

The project's architecture is defined by the OpenAPI specification located in the `contracts` directory. This specification details all the available endpoints, data models, and interactions between the different services.

### Repositories

Here is a list of the repositories that make up the Meetinity project, along with a brief description of their role and current status:

| Repository | Description | Status |
|---|---|---|
| **meetinity** | Main repository containing the API contracts (OpenAPI) and this main README. | 15% - Specifications defined, no implementation. |
| **meetinity-mobile-app** | A mobile application built with React, allowing users to interact with the platform. | 70% - Functional application with OAuth authentication. |
| **meetinity-admin-portal** | An administration portal for managing the platform, built with React. | 60% - Admin interface with data visualization components. |
| **meetinity-api-gateway** | An API gateway built with Flask, responsible for routing requests to the appropriate microservices. | 40% - Basic structure with JWT middleware implemented. |
| **meetinity-user-service** | A user management service built with Flask, handling authentication and user profiles. | 80% - Complete service with OAuth and JWT. |
| **meetinity-matching-service** | A service for matching users based on their profiles and interests, built with Flask. | 25% - Basic logic implemented with mocked data. |
| **meetinity-event-service** | A service for managing professional events, built with Flask. | 35% - Basic REST API with data validation. |

## Getting Started

To get started with the Meetinity project, you will need to clone each of the repositories listed above. You can then follow the instructions in each repository's README file to install the dependencies and run the services.

## Global Progress

- **Frontend**: 65% (Mobile app + Admin portal)
- **Backend**: 45% (API Services)
- **Infrastructure**: 20% (No deployment configured yet)
- **Documentation**: 40% (API specifications and partial code documentation)

**Overall Estimated Progress: 45%**

The project has a solid foundation with a well-defined architecture and functional components. The main focus should now be on integrating the services with a real database and setting up the production environment.


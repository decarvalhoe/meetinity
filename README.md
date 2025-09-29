[English](README.md) | [Français](README.fr.md)

# 🤝 Meetinity - Professional Networking Platform

A modern professional networking platform designed to help users **connect**, **discover events**, and **grow their professional network**. This open-source project enables meaningful professional relationships through intelligent matching and event discovery.

## 🎯 What is Meetinity?

Meetinity is a comprehensive networking platform that allows you to:

- **Connect with professionals** through intelligent matching algorithms
- **Discover relevant events** in your industry and location
- **Build meaningful relationships** with like-minded professionals
- **Manage your professional profile** with OAuth authentication

### Why choose Meetinity?

- ✅ **Modern Architecture**: Scalable microservices with React frontends
- ✅ **Secure Authentication**: OAuth 2.0 with Google and LinkedIn integration
- ✅ **Intelligent Matching**: Advanced algorithms for professional connections
- ✅ **Event Discovery**: Comprehensive event management and discovery system
- ✅ **Open Source**: Transparent and community-driven development

## 🚀 Project Status

### Phase 1: Authentication & Core Infrastructure (✅ Completed - 80%)
**Objective**: Establish secure user management and basic platform infrastructure

- ✅ **OAuth Authentication**: Google and LinkedIn integration with JWT
- ✅ **User Profile Management**: Complete CRUD operations for user profiles
- ✅ **Mobile Application**: React-based mobile app with authentication UI
- ✅ **Admin Portal**: User management dashboard with filtering and analytics
- ✅ **API Gateway**: Request routing and JWT middleware

*Result*: Solid foundation with secure authentication and user management capabilities.

### Phase 2: Event Management (🔄 In Progress - 35%)
**Objective**: Enable event creation, discovery, and registration

- 🔄 **Event Service**: REST API with data validation (needs database integration)
- 📋 **Event Registration**: User registration and attendance tracking
- 📋 **Event Discovery**: Advanced search and filtering capabilities

*Expected Result*: Users will be able to create, discover, and register for professional events.

### Phase 3: Professional Matching (🔄 In Progress - 25%)
**Objective**: Connect professionals through intelligent algorithms

- 🔄 **Matching Algorithms**: Profile-based compatibility scoring
- 📋 **Swipe Interface**: Tinder-like interaction for professional connections
- 📋 **Real-time Matching**: Instant notifications for mutual connections

### Phase 4: Communication & Networking (📋 Planned)
**Objective**: Enable communication between matched professionals

- 📋 **Messaging System**: Real-time chat between matched users
- 📋 **Conversation Management**: Thread organization and history
- 📋 **Notification System**: Push notifications for matches and messages

## 🛠️ For Developers

### Quick Start

```bash
# 1. Clone the project
git clone https://github.com/decarvalhoe/meetinity.git
cd meetinity

# 2. Set up development environment
make setup

# 3. Start all services
make dev-up

# 4. Check service health
curl http://localhost:5000/health

# 5. Stop the environment
make dev-down
```

### Technical Architecture

The project uses a modern **microservices architecture**. All backend services now live in the [`services/`](services/) directory to streamline local development and deployments:

- **API Gateway** (`services/api-gateway`): Flask-based request routing and authentication
- **User Service** (`services/user-service`): OAuth authentication and profile management
- **Event Service** (`services/event-service`): Event creation, discovery, and registration
- **Matching Service** (`services/matching-service`): Professional matching algorithms and swipe functionality
- **Mobile App**: React 18 with TypeScript and Vite
- **Admin Portal**: React-based administration interface
- **Database**: PostgreSQL for data persistence
- **Cache**: Redis for performance optimization

### Cloud Infrastructure Enhancements

Our infrastructure baseline is now fully documented and automated:

- **Static assets CDN**: Private S3 bucket fronted by CloudFront with optional custom domains.
- **Shared load balancers**: Pre-provisioned ALB (HTTP/HTTPS) and NLB (TCP) endpoints for workloads that cannot rely on the ingress controller.
- **Automated backups**: Daily AWS Backup plan covering the Aurora PostgreSQL cluster with configurable retention.
- **Cost monitoring**: Monthly AWS Budget notifications to alert the platform team and finance stakeholders.
- **Infrastructure as Code**: Terraform modules, Helm charts, and deployment scripts described in [`docs/cloud-operations.md`](docs/cloud-operations.md), [`docs/containerization-roadmap.md`](docs/containerization-roadmap.md), [`docs/observability.md`](docs/observability.md), and [`docs/autoscaling-playbook.md`](docs/autoscaling-playbook.md).

### Repository Structure & Progress

| Component | Location | Status |
|---|---|---|
| **Documentation & Contracts** | `docs/`, `contracts/` | 25% – Core specifications consolidated, awaiting final data models |
| **API Gateway** | `services/api-gateway` | 45% – Auth pass-through and routing ready, needs coverage for event/messaging flows |
| **User Service** | `services/user-service` | 80% – OAuth + profiles stable, pending messaging profile hooks |
| **Event Service** | `services/event-service` | 40% – REST API scaffolding complete, registration storage outstanding |
| **Matching Service** | `services/matching-service` | 30% – Matching logic prototype, requires data sync with events/users |
| **Messaging (planned)** | `services/` (new) | 10% – Container baseline prepared, functionality to be implemented |
| **Mobile App** | External repo `meetinity-mobile-app` | 70% – Authentication and discovery UI shipped |
| **Admin Portal** | External repo `meetinity-admin-portal` | 60% – User management complete |

## 🤝 How to Contribute?

We welcome all contributions! Whether you are:

- **Professional Networker**: Share insights on networking best practices
- **Developer**: Improve code quality and add new features
- **Designer**: Enhance user experience and interface design
- **Tester**: Help identify and fix bugs across the platform

### Steps to Contribute

1. **Review** the [open issues](https://github.com/decarvalhoe/meetinity/issues) and [project roadmap](TODO.md)
2. **Read** the contribution guide in `CONTRIBUTING.md`
3. **Create** a feature branch for your contribution
4. **Submit** a pull request with your improvements

## 📊 2025 Evaluation & Roadmap

A comprehensive technical evaluation was conducted in September 2025, revealing strong foundations with strategic opportunities for growth.

- **Key Strengths**: Robust OAuth authentication, modern React frontends, clean microservices architecture
- **Critical Issues**: Event registrations, cross-service data synchronisation, and messaging flows still pending
- **Priority Actions**: Expand gateway coverage, deliver registrations & matching data sync, implement networking features

Find the detailed evaluation and strategic roadmap in [`docs/project-evaluation.md`](docs/project-evaluation.md), [`docs/cloud-operations.md`](docs/cloud-operations.md), and [`TODO.md`](TODO.md).

## 📞 Support and Community

- **GitHub Issues**: Report bugs or suggest features
- **Discussions**: Engage with the community
- **Documentation**: Complete guides in the `docs/` folder

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for more details.

---

> **Built with ❤️ by decarvalhoe and the open-source community**  
> **Overall Progress: 45%** | Last updated: September 2025

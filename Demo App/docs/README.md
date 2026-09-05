# Demo Commerce Application

## Overview

The Demo Commerce Application is a fully functional, production-ready mock e-commerce platform designed to demonstrate the capabilities of the **Agentic Commerce Copilot**. It serves as the "merchant" website where users can browse laptops and electronics, add items to their cart, and complete a checkout process using Razorpay.

This application acts as the testing ground and integration point for the Agentic Copilot, providing real-time behavioral events, a product catalog, and backend commerce APIs that the Copilot's engines and agents interact with.

## Purpose

The primary purpose of the Demo App is to:
1. Provide a realistic e-commerce environment (Frontend + Backend) to showcase AI-driven commerce.
2. Emit real-time customer behavior events (e.g., browsing, searching) to the Copilot.
3. Expose RESTful APIs for the Copilot's `CommerceEngine` to read the product catalog, manage carts, and process simulated checkouts.
4. Demonstrate a seamless handoff between an AI Sales Consultant (Voice/Telegram) and a traditional web checkout flow.

## Key Features

- **Product Catalog**: A rich database of laptops and accessories, categorized and searchable.
- **Cart & Checkout**: Full cart management (anonymous and authenticated) with subtotal, tax, and shipping calculations.
- **Payment Integration**: Complete integration with Razorpay for handling test payments and verifying signatures.
- **Behavioral Telemetry**: A built-in event tracking system that logs user actions (page views, searches) and sends them to the Copilot for intent detection.
- **Wishlist & User Accounts**: Standard user authentication (JWT), address management, and wishlist functionality.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 & Alembic
- **Authentication**: JWT (JSON Web Tokens) with Passlib (Bcrypt)
- **Payments**: Razorpay Python SDK

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4 + Framer Motion
- **UI Components**: Radix UI + Lucide React
- **State Management**: Zustand
- **Data Fetching**: Axios & TanStack React Query

## Application Structure

- `frontend/`: Contains the React web application.
- `backend/`: Contains the FastAPI server, database models, and API endpoints.

## Documentation Navigation

- [Architecture & Design](architecture.md)
- [Application Flow](application-flow.md)
- [Database Schema](database.md)
- [REST API](api.md)
- [Setup & Configuration](setup.md)

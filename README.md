# AegisCart

**A trust layer for agentic commerce.**

AegisCart is an experimental agentic-commerce project being built for **Razorpay AI Buildathon 2026 – Track 01: AI Growth & Agentic Commerce**.

The idea explores a simple question:

> What happens when the customer making a purchase is an AI agent?

AI agents can understand preferences and recommend products, but financial actions need stronger boundaries. AegisCart is being designed so that an AI can help discover and evaluate products while the user's spending rules remain in control.

## Core Idea

The planned flow is:

**User Request → Buyer Agent → Merchant Agent → Product Recommendation → Policy Check → Human Approval → Payment → Audit Receipt**

A key part of the project is the **AI Purchase Constitution** — a set of user-defined rules such as:

* maximum autonomous spending amount
* purchases that require human approval
* maximum allowed upsell
* delivery constraints
* hard spending limits

The AI can reason about a purchase, but deterministic rules decide whether the financial action is actually allowed.

## Current Status

🚧 **Early development**

The project structure and architecture are currently being set up. Features and documentation will be updated as they are implemented and tested.

## Planned Stack

* React + Vite
* Python + FastAPI
* LLM-based agent reasoning
* SQLite
* Razorpay Test Mode
* Git & GitHub

## Design Principle

> **Separate probabilistic AI reasoning from deterministic financial authorization.**

## Build Log

This repository will document not only what works, but also important failures, design changes, and lessons discovered while building the project.

<div align="center">
  <br>
  <h1><b>ALX Travel App - Milestone 4: Payment Integration with Chapa API </b></h1>
</div>
<br />

---
## Table of Contents

- [Table of Contents](#table-of-contents)
  - [Objectives](#objectives)
  - [Key Concepts:](#key-concepts)
  - [Tools and Libraries](#tools-and-libraries)


<br />

---

### Objectives

This document details the integration of the Chapa Payment Gateway into a Django-based travel booking application.

- Configure and securely store API credentials for third-party payment gateways.
- Create Django models to manage and track payment transactions.
- Build API endpoints for payment initiation and verification.
- Implement payment workflows integrated into a booking system.
- Handle payment status updates and transaction logging.
- Test payment flows using a sandbox environment.


<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---

### Key Concepts:

- **API Integration** – Connecting Django with the Chapa API for payment processing.
- **Secure Credential Management** – Storing API keys in environment variables.
- **Django Models** – Structuring and persisting payment transaction data.
- **HTTP Requests** – Sending POST and GET requests to initiate and verify payments.
- **Asynchronous Tasks** – Using Celery for sending confirmation emails.
- **Error Handling** – Managing failed or incomplete payments gracefully.



<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---

### Tools and Libraries

- **Django** – Backend framework for building the application.
- **PostgreSQL** – Database for persisting bookings and payment data.
- **Chapa API** – Payment gateway for initiating and verifying transactions.
- **Requests** – Python library for making API calls to Chapa.
- **Celery** – For background email sending after successful payment.
- **dotenv** – For managing environment variables securely.


<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>


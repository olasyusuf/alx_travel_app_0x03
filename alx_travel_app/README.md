<div align="center">
  <br>
  <h1><b>ALX Travel App - Milestone 3: API Endpoints</b></h1>
</div>
<br />

---
## Table of Contents

- [Table of Contents](#table-of-contents)
  - [Objectives](#objectives)
  - [API Endpoints](#api-endpoints)
  - [API Documentation](#api-documentation)


<br />

---

### Objectives

This document details the design and implementation of Travel App API views to manage listings and bookings, and ensure the endpoints are documented with Swagger.

- Create ViewSets
- Configure URLs
- Test Endpoints

<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---

This milestone implements:


- CRUD operations for **Listings** and **Bookings**
- RESTful API endpoints using Django REST Framework
- Auto-generated API docs with Swagger (drf-yasg)
- JSON responses with proper validation
- Modular code with ViewSets and Routers


<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---

### API Endpoints

All API endpoints are accessible under:

http://127.0.0.1:8000/api/

Method	Endpoint	Description
- `GET	/api/listings/`	List all listings
- `GET	/api/listings/{listing_id}`	Get a listing with the listing_id
- `POST	/api/listings/`	Create new listing
- `PUT /api/listings/{listing_id}` Update a Listing
- `DEL /api/listings/{listing_id}` Delete a Listing
- `GET	/api/bookings/`	List all bookings
- `POST	/api/bookings/`	Create new booking

<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---

### API Documentation

Method	Endpoint	Description
- `GET	/api/swagger/`	
- `GET	/api/redoc/`	

<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---
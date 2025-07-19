<div align="center">
  <br>
  <h1><b>ALX Travel App - Milestone: Models, Serializers, and Seeder</b></h1>
</div>
<br />

---
## Table of Contents

- [Table of Contents](#table-of-contents)
  - [Objectives](#objectives)
  - [Models Overview](#models-overview)
  - [Seeder Command](#seeder-command)


<br />

---

### Objectives

This document details the design and implementation of Travel App database models, the creation of serializers for REST API data representation, and the implementation of a management command to seed the database.

- Create Models
- Set Up Serializers
- Implement Seeders
- Run Seed Command


<br />

---

This milestone implements:

- **Users, Listing, Booking, and Review models** with appropriate relationships and fields.
- **Serializers** for Listing and Booking to support API endpoints.
- **Custom seeder command** to populate the database with sample listings.

### Models Overview

- **Users**: `role`, `first_name`, `last_name`, `password`, `email`, `phone_number`, `created_at`
- **Listing**: `title`, `description`, `location`, `price_per_night`, `is_available`, `watchlist`, `created_at`, `updated_at`
- **PropertyFeature**: ForeignKey to `Listing`, `name` of feature, `qty`, `created_at`
- **Booking**: ForeignKey to `Listing` &`Users`, `start_date`, `end_date`, `total_price`, `status`, 
- **Review**: ForeignKey to `Listing` & `Users`, `rating`, `comment`

### Seeder Command

To populate database with demo listings:
```
python manage.py seed

```

<br />

<div align="right">

  [ [↑ to top ↑](#table-of-contents) ]
</div>

---
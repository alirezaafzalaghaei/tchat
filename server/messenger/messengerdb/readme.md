# Messenger Database

This folder contains a subpackage for implementing the database structure of TChat. It includes:

- `messenger.py`: Implements models and tables.
- `__init__.py`: Uses BearType for statically type-checking function input values.

## Details of `messenger.py`

The models and tables of this chat application are implemented using a Flask-compatible version of SQLAlchemy. The models include:

- **User model**, including:
    - `id` (primary key)
    - `username`
    - `name`
    - `password`
    - `email`
    - `created_at` (or join time)
- **PublicRoomMessages**
    - `id` (primary key)
    - `user_id` (foreign key)
    - `message`
    - `room_name` (in the current application, the only room is `public_room`)
    - `timestamp`
- **UserChat**
    - `id` (primary key)
    - `sender_id` (foreign key)
    - `receiver_id` (foreign key)
    - `message`
    - `timestamp`
- **Session**
    - `session_id`
    - `user_id` (foreign key)
    - `login_time`

These tables and their relationships are managed by the `Messenger` class, which is used by the Flask app.

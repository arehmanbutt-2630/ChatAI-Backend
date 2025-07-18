#!/bin/bash

# Run database migrations
flask db upgrade

# Start the server
exec flask run --host=0.0.0.0 --port=5000

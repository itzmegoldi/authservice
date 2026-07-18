#!/usr/bin/env sh
set -e

alembic upgrade head
sleep 20
python -m src.api.main


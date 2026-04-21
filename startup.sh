#!/bin/bash
set -e
python -m alembic upgrade head
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0

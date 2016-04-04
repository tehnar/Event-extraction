#!/usr/bin/env python3
from db import DatabaseHandler
import web_ui

from web_ui import app
app.db_handler = DatabaseHandler()
app.run(debug=True)
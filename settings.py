"""Settings used by the application."""

import pandas as pd
import plotly.io as pio

# Data Configuration
# ==================
# Set these to match your data files
YEAR = "2016"        # Year of your route data (e.g., "2016", "2017")
BOARD = "moonboard"  # Board type (e.g., "moonboard")

# Expected data files:
# - data/routes_input/{YEAR}_{BOARD}.json or .pkl (required)
# - data/hold_scores/{YEAR}_{BOARD}_manual.csv (optional, for manual classifications)
#
# See DATA.md for detailed format specifications

# Output Configuration
# ====================
VERBOSE = True  # Enable detailed logging and visualizations

# Pandas and Plotting Settings
# ============================
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1500)

pio.renderers.default = "browser"
# Fix rendering bug
pio.kaleido.scope.mathjax = None


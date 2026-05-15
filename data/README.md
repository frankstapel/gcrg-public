# Data Directory

This directory contains your route data and generated analysis files.

## Directory Organization

```
data/
├── routes_input/      # Your route data files (place your data here)
├── hold_scores/       # Hold difficulty classifications (generated and manual)
├── routes/            # Processed route dataframes (generated)
├── move_scores/       # Move scoring analysis (generated)
├── sequences/         # Route sequences (generated)
├── sequencer/         # Working files (generated)
└── models/            # Trained models (generated)
```

## Where to Place Your Data

### Required: Route Data
Place your route data file in `data/routes_input/`:

**Option 1: JSON Format**
```
data/routes_input/2016_moonboard.json
```

**Option 2: Pickle Format**
```
data/routes_input/2016_moonboard.pkl
```

See [../DATA.md](../DATA.md) for detailed format specifications.

### Optional: Manual Hold Classifications
If you have manually classified hold difficulties, place them here:
```
data/hold_scores/2016_moonboard_manual.csv
```

## Generated Files

The following files will be created automatically when you run `main.py`:

- `data/routes/2016_moonboard_routes.pkl` - Processed routes
- `data/hold_scores/2016_moonboard_hold_scores.pkl` - Computed hold difficulties
- `data/move_scores/2016_moonboard_moves.pkl` - Move analysis
- `data/models/` - Trained machine learning models

## Configuration

Update `settings.py` in the project root:

```python
YEAR = "2016"           # Match your data year
BOARD = "moonboard"     # Board type
```

The code will automatically look for:
- `data/routes_input/{YEAR}_{BOARD}.json` or `.pkl`
- `data/hold_scores/{YEAR}_{BOARD}_manual.csv` (optional)

And generate:
- `data/routes/{YEAR}_{BOARD}_routes.pkl`
- `data/hold_scores/{YEAR}_{BOARD}_hold_scores.pkl`
- etc.

## Next Steps

1. Prepare your route data in the correct format (see [../DATA.md](../DATA.md))
2. Place it in `data/routes_input/`
3. Update `settings.py`
4. Run `python main.py` from the project root

For detailed format specifications, see [../DATA.md](../DATA.md)

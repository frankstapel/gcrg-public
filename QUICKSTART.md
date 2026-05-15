# Quick Start Guide

## For Researchers Using This Code

### 1. **Prepare Your Data**
   - Export your climbing route data to JSON or pickle format
   - See [DATA.md](DATA.md) for exact format specifications
   - Place your data in `data/routes_input/`

### 2. **Name Your Data File**
   - Format: `{YEAR}_{BOARD}.json` or `.pkl`
   - Example: `2023_moonboard.json`

### 3. **Update Settings**
   ```python
   # settings.py
   YEAR = "2023"        # Match your file name
   BOARD = "moonboard"  # Board type
   ```

### 4. **Run the Analysis**
   ```bash
   python main.py
   ```
   This will:
   - Process your routes
   - Calculate hold difficulties
   - Train move scoring models
   - Generate optimal route sequences

### 5. **Access Results**
   Results are saved in:
   - `data/hold_scores/{YEAR}_{BOARD}_hold_scores.pkl` - Hold difficulties
   - `data/routes/{YEAR}_{BOARD}_routes.pkl` - Processed routes
   - `plots/` - Visualizations

## Data Format Quick Reference

### JSON Format (Easiest)
```json
[
  {
    "Grade": "5B",
    "Moves": ["A1", "B3", "D5"]
  }
]
```

### Pickle Format
```python
{
  "route_0": {
    "grade": "5B",
    "start": [[0, 0], [10, 0]],
    "mid": [[5, 8]],
    "end": [[3, 16]]
  }
}
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "Could not find data file" | Check your file is named `{YEAR}_{BOARD}.json` or `.pkl` |
| File in wrong location | Put data in `data/routes_input/`, not `data/` root |
| Settings YEAR doesn't match file | Update `settings.py` YEAR to match your filename |
| Routes are 3D lists | Use 2D coordinates: `[col, row]` not `[[x, y, z]]` |
| Grades not recognized | Use Font grade system (5A, 5A+, 5B, etc.) |

## Coordinate System

**MoonBoard Grid (Standard)**
- Columns: 0-10 (or A-K)
- Rows: 0-17

**Conversion:**
- Letter to number: A→0, B→1, ..., K→10
- Row: 1→0, 2→1, ..., 18→17

## File Structure After Running

```
data/
├── routes_input/
│   └── 2023_moonboard.json  (your input)
├── routes/
│   └── 2023_moonboard_routes.pkl   (generated)
├── hold_scores/
│   └── 2023_moonboard_hold_scores.pkl  (generated)
├── move_scores/
│   ├── 2023_moonboard_moves.pkl    (generated)
│   └── 2023_moonboard_performance.csv
├── models/
│   ├── moves/    (trained models)
│   └── ord_to_font/
└── sequences/    (generated sequences)
```

## Next Steps

1. **Explore the code**: Check `classification/` and `sequencing/` modules
2. **Customize analysis**: Modify scoring functions in `sequencing/move_scoring.py`
3. **Train different models**: Try different classifiers in `classification/move_scores.py`
4. **Cite your work**: See [DATA_LICENSING.md](DATA_LICENSING.md) for citation guidelines

## Help & Documentation

- **Data formats**: [DATA.md](DATA.md)
- **Full README**: [README.md](README.md)
- **Settings**: See comments in `settings.py`

## Citation

If you publish research using this code, please cite this repository and your data source.

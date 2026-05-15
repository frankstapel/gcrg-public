# gcrg-public
Grade Classification and Route Generation for Training Boards

## Introduction
This project provides tools for analyzing climbing training board routes and generating grade classifications. It supports processing route data to extract hold difficulties, score climbing moves, and generate optimal sequences for routes.

The code is designed to be used with your own climbing route data, making it reusable for researchers and developers analyzing climbing training boards.

**Note**: This is research code developed as part of an academic project. While well-tested, it may contain bugs or assumptions specific to the original research context. Users are responsible for validating results for their own use cases.

## Quick Start

### Prerequisites
- Python 3.8+
- A climbing route dataset (JSON or pickle format - see [DATA.md](DATA.md))

### Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`

### Usage

1. **Prepare your data**: Follow the [DATA.md](DATA.md) guide to format your climbing route data
2. **Configure settings**: Edit `settings.py` to specify your data year and board type
3. **Run the analysis**: 
   ```bash
   python main.pyy
   ```

This will:
- Process your raw route data
- Calculate hold difficulty scores based on route grades
- Train models to score climbing moves
- Generate optimal sequences for each route

## Project Structure

```
.
├── classification/        # Grade classification and scoring
│   ├── hold_scores.py    # Calculate hold difficulty scores
│   ├── move_scores.py    # Train move difficulty models
│   └── route_scores.py   # Score complete routes
├── sequencing/            # Route sequencing and analysis
│   ├── move_scoring.py   # Score individual climbing moves
│   ├── route_sequencer.py # Generate optimal move sequences
│   ├── sequence.py       # Sequence data structures
│   └── search.py         # Beam search algorithm
├── helpers/               # Utility functions
│   ├── moonboard.py      # MoonBoard-specific logic
│   ├── grade_conversion.py # Grade system conversions
│   ├── files.py          # File I/O operations
│   └── moonboard_gui.py  # GUI utilities
├── generation/            # Route generation
├── media/                 # Board layouts and fonts
├── plots/                 # Visualization outputs
├── data/                  # Data directory (user-provided and generated)
├── settings.py           # Configuration
├── main.py               # Entry point
└── requirements.txt      # Python dependencies
```

## Data and Configuration

### Required Data
- **Route dataset**: See [DATA.md](DATA.md) for format specifications
- **Format**: JSON or pickle file with route grades and hold coordinates

### Configuration
Edit `settings.py`:
```python
YEAR = "2016"        # Data year
BOARD = "moonboard"  # Board type
VERBOSE = True       # Enable detailed logging
```

## Key Modules

### Classification
- **hold_scores.py**: Analyzes which holds are difficult vs. easy based on route grades
- **move_scores.py**: Trains models to predict move difficulty
- **route_scores.py**: Scores complete routes using trained models

### Sequencing
- **route_sequencer.py**: Generates optimal climbing sequences using beam search
- **move_scoring.py**: Scores individual moves based on hold position and difficulty
- **sequence.py**: Data structures for hold sequences

### Helpers
- **moonboard.py**: MoonBoard coordinate system and visualization
- **grade_conversion.py**: Converts between grade systems (Font, IRCRA, ordinal)

## Output

The analysis generates:
- `data/hold_scores/{YEAR}_{BOARD}_hold_scores.pkl` - Hold difficulty classification
- `data/routes/{YEAR}_{BOARD}_routes.pkl` - Processed route data
- `data/move_scores/` - Move scoring analysis
- `data/sequences/` - Generated route sequences
- Visualizations in `plots/`

## Development and Contributing

This code is structured for research and experimentation. Key customization points:
- Add new board types by extending `helpers/moonboard.py`
- Modify move scoring in `sequencing/move_scoring.py`
- Adjust grade classifications in `classification/hold_scores.py`
- Train different models in `classification/move_scores.py`

## Citation:

```bibtex
@software{gcrg_2022,
  title={Grade Classification and Route Generation},
  author={Stapel, Frank},
  year={2022},
  url={https://github.com/frankstapel/gcrg-public}
}
```

If you use this code in your research, please cite this repository. See [LICENSE](LICENSE) for terms of use.

## Data Attribution

This project is designed to work with your own data. **Ensure you have permission to use any data you analyze with this code.** If using publicly available climbing data, respect the original source's licensing terms.

## License

See [LICENSE](LICENSE) file for licensing information.

## FAQ

**Q: Can I use this with data other than MoonBoard?**
A: The code is primarily designed for MoonBoard, but can be adapted for other board types by modifying `helpers/moonboard.py`.

**Q: What if I don't have manual hold classifications?**
A: Manual classifications are optional. The code will compute hold difficulties automatically from route grades.

**Q: How much data do I need?**
A: Minimum ~500 unique routes recommended for reliable statistical analysis. More data improves model quality.

**Q: The code runs but gives errors about missing files.**
A: Check [DATA.md](DATA.md) to ensure your data is in the correct format and location.

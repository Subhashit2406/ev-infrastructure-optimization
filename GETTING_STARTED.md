# Getting Started

This document provides quick setup instructions for the EV Infrastructure Optimization project.

## Prerequisites

- **Python 3.8 or higher**
- **pip** (Python package manager)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ev-infrastructure-optimization.git
cd ev-infrastructure-optimization
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download Datasets (Optional)

The project includes synthetic data by default. To download real datasets from Kaggle:

```bash
python download_datasets.py
```

Note: You'll need Kaggle API credentials. See [Kaggle API documentation](https://github.com/Kaggle/kaggle-api).

## Quick Start

### Run the Complete Pipeline

```bash
python main.py --all
```

This runs all 4 phases:
1. **Phase 1**: Demand Forecasting
2. **Phase 2**: Geospatial Clustering
3. **Phase 3**: Grid Load Optimization
4. **Phase 4**: Financial Analysis

### Run Individual Phases

```bash
# Phase 1 only
python main.py --phase 1

# Phase 2 only
python main.py --phase 2

# Phase 3 only
python main.py --phase 3

# Phase 4 only
python main.py --phase 4
```

### Data Processing Only

```bash
python main.py --process
```

### Launch the Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Project Structure

```
ev-infrastructure-optimization/
│
├── main.py                 # Main entry point
├── app.py                  # Streamlit dashboard
├── download_datasets.py    # Data download utility
├── requirements.txt        # Python dependencies
│
├── src/                    # Source code
│   ├── data/              # Data loading & processing
│   ├── features/          # Feature engineering
│   ├── models/            # ML models & optimization
│   └── visualization/     # Plotting utilities
│
├── data/                  # Datasets
│   ├── raw/              # Original data
│   └── processed/        # Processed data
│
├── results/              # Model outputs
│   ├── phase1_forecasting/
│   ├── phase2_geospatial/
│   ├── phase3_optimization/
│   └── phase4_financial/
│
├── notebooks/            # Jupyter notebooks
├── comprehensive_ev_data/# Additional datasets
└── interactive_plots/    # Generated visualizations
```

## Output Files

After running the pipeline, you'll find:

- **Results**: `results/` directory with JSON outputs
- **Visualizations**: `infrastructure_model_plots/` and `interactive_plots/`
- **Processed Data**: `data/processed/` with cleaned datasets

## Troubleshooting

### ImportError or Missing Modules

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt --upgrade
```

### Data Not Found

```bash
# Process data from included synthetic datasets
python main.py --process

# Or download new datasets
python download_datasets.py
```

### Streamlit Issues

```bash
# Clear Streamlit cache
streamlit cache clear

# Run dashboard with verbose output
streamlit run app.py --logger.level=debug
```

## Configuration

### Modify Parameters

Key parameters can be configured in the source files:

- **Forecasting**: `src/models/forecasting.py`
- **Clustering**: `src/models/clustering.py`
- **Optimization**: `src/models/optimization.py`
- **Financial Analysis**: `src/models/financial.py`

## Next Steps

1. **Read the [README.md](README.md)** for project overview
2. **Check [CONTRIBUTING.md](CONTRIBUTING.md)** if you want to contribute
3. **Explore the [CHANGELOG.md](CHANGELOG.md)** for version history
4. **Review the dashboard** insights by running `streamlit run app.py`

## Support

- **Issues**: [Create an issue on GitHub](https://github.com/yourusername/ev-infrastructure-optimization/issues)
- **Questions**: Check existing issues and discussions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

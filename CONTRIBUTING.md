# Contributing to EV Infrastructure Optimization

We welcome contributions to make this project better! Here's how you can help.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ev-infrastructure-optimization.git
   cd ev-infrastructure-optimization
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Feature branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `perf/` - Performance improvements

### Making Changes

1. Make your changes in the appropriate module under `src/`
2. Follow PEP 8 style guidelines
3. Add docstrings to all functions and classes
4. Test your changes:
   ```bash
   python main.py --phase 1  # or specific test command
   ```

### Committing Your Changes

Use clear, descriptive commit messages:
```bash
git commit -m "feat: add new clustering algorithm"
git commit -m "fix: resolve data loading issue"
git commit -m "docs: update README with new examples"
```

## Code Standards

### Style Guide
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions
- Use type hints where applicable
- Write docstrings using Google style format

### Docstring Example
```python
def calculate_optimal_location(demand_data: pd.DataFrame) -> dict:
    """
    Calculate optimal EV charging station locations.
    
    Args:
        demand_data: DataFrame with demand metrics
        
    Returns:
        Dictionary with recommended locations and scores
        
    Raises:
        ValueError: If demand_data is empty
    """
```

## Reporting Issues

### Before Creating an Issue
- Check if the issue already exists
- Provide a clear title and description
- Include Python version and OS information
- Provide steps to reproduce the issue

### Issue Template
```markdown
**Description**
Brief description of the issue

**Steps to Reproduce**
1. ...
2. ...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- Python: 3.x
- OS: Windows/macOS/Linux
```

## Pull Request Process

1. **Update your branch** with latest changes:
   ```bash
   git pull origin main
   git rebase main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to related issues (if any)
   - Testing confirmation

4. **PR Template**:
   ```markdown
   ## Description
   Brief overview of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   
   ## Testing Done
   Description of how you tested
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] Tests added/updated
   ```

### PR Review Process
- At least one review required before merge
- All CI/CD checks must pass
- No merge conflicts

## Project Structure

```
ev-infrastructure-optimization/
├── src/
│   ├── data/           # Data loading and processing
│   ├── features/       # Feature engineering
│   ├── models/         # ML models and optimization
│   └── visualization/  # Plotting utilities
├── data/
│   ├── raw/            # Original datasets
│   └── processed/      # Processed data
├── results/            # Model outputs and visualizations
├── main.py             # Entry point
├── app.py              # Streamlit dashboard
└── requirements.txt    # Dependencies
```

## Common Tasks

### Adding a New Model

1. Create file in `src/models/`:
   ```python
   # src/models/my_model.py
   
   def train_model(data):
       """Train new model"""
       pass
   
   def run_pipeline():
       """Main pipeline function"""
       # Call from main.py via this function
       pass
   ```

2. Update `main.py` to call your pipeline

### Adding a New Feature

1. Create file in `src/features/`:
   ```python
   # src/features/new_feature.py
   
   def engineer_feature(df):
       """Engineer new feature"""
       pass
   ```

2. Update data processing pipeline to use it

## Testing

Run the main pipeline:
```bash
python main.py --all
```

Run specific phase:
```bash
python main.py --phase 1
```

## Documentation

- Update [README.md](README.md) for major changes
- Add docstrings to all new functions
- Update this file if workflow changes

## Questions?

- Create an issue for questions
- Check existing issues and discussions first
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🚗⚡

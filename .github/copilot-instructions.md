# Copilot Instructions for Taxi Prediction Project

## Project Overview
This is a data science project implementing a taxi trip demand prediction system using LightGBM. The codebase demonstrates production ML engineering practices from the book "先輩データサイエンティストからの指南書" (Tech Review Corp).

## Architecture & Key Components

### Core ML Pipeline (`src/taxi_prediction/`)
- **`schema.py`**: Pandera dataframe schemas that enforce type safety and data validation throughout the pipeline
  - `TaxiDatasetSchema`: Raw dataset format (date, area, num_trip)
  - `TrainInputSchema`: Features for training with target variable
  - `InferInputSchema`: Features for inference (no target)
  - Used with `@pa.check_types` decorator to validate function inputs/outputs
- **`process.py`**: Data processing functions with schema enforcement
  - `load_dataset()`: Reads CSV with date parsing and categorical conversion
  - `split_dataset()`: Time-series aware split maintaining temporal order
  - `preprocess_for_infer()`: Feature engineering (adds weekday, target_lead, target_date)
  - `preprocess_for_train()`: Adds target variable via join on target_date
- **`model.py`**: LGBModel wrapper class using LightGBM Booster
  - `fit()`: Trains with early stopping on validation set
  - Data split: drop target column for features, use separate label
  - Logs metrics during training via `lgb.log_evaluation()`
- **`consts.py`**: Project constants (MAX_PREDICT_DAYS = 7)

### Data Flow
1. Raw CSV (date, area, num_trip) → loaded via `load_dataset()`
2. Time-series split into train/valid sets
3. Feature engineering: Creates N rows per original row (one per target_lead 1-7)
4. Multi-step forecasting: Predicts demand 1-7 days ahead

### Configuration & Experiment Tracking
- **`scripts/conf/config.yaml`**: Hydra config (data_path, train_ratio=0.7, model params, train params)
- **`scripts/train_with_mlflow.py`**: Main training script
  - Uses Hydra for config management (`@hydra.main()`)
  - MLflow tracking URI: `file:///app/mlruns` (local file-based)
  - Logs params, tables (df_train.json, df_valid.json), metrics, and model artifact

### Environment & Deployment
- **`Dockerfile`**: Python 3.12-slim with uv package manager
  - System deps: graphviz, ca-certificates, git, locale support
  - UV_PROJECT_ENVIRONMENT="/usr/local/" for system Python usage
- **`compose.yml`**: Single service with volume mount, port 8501 (Streamlit default)

## Development Conventions

### Data Validation First
- All processing functions use Pandera schemas with `@pa.check_types` decorator
- Schemas use Field constraints (ge=0, in_range, max_value)
- Custom dataframe checks: `@pa.dataframe_check` for cross-field validations
- Config: `strict=True, coerce=True` to catch schema violations early

### Naming Patterns
- Dataframe variables: prefix with `df_` (df_train, df_valid, df_result)
- Schemas: suffix with `Schema` (TrainInputSchema, InferInputSchema)
- Functions: verb-first action names (load_dataset, preprocess_for_train, split_dataset)
- Config files: YAML under `scripts/conf/` with Hydra discovery

### Testing
- Test fixtures in `tests/taxi_prediction/test_process.py`
- Sample data as CSV strings in fixtures
- Use `pandas.testing.assert_frame_equal()` for assertion
- Pandera types in test function signatures

## Critical Workflows

### Training
```bash
python scripts/train_with_mlflow.py  # Uses Hydra config auto-discovery
```
- Reads config from `scripts/conf/config.yaml` and merges CLI overrides
- MLflow outputs go to `mlruns/` (local directory)
- Model saved as `model.pickle` and logged to MLflow

### Viewing Experiments
- MLflow runs stored in `mlruns/` directory
- Each run has subdirectory with artifacts, metrics, params, tags

### Running Tests
```bash
pytest tests/
```

### Dependencies & Package Management
- Uses **uv** (Astral project manager) in Docker
- `pyproject.toml`: Specifies Python >=3.12,<3.13
- Key deps: lightgbm, pandera, mlflow, hydra-core, pandas, scikit-learn
- Dev deps: pytest, mypy, jupyter, japanize-matplotlib
- Install via uv: `uv sync` or `uv pip install`

## Cross-Component Integration Points

### Hydra Configuration
- Config path discovery: `config_path="conf"` in `train_with_mlflow.py`
- Overrides: `python scripts/train_with_mlflow.py train_ratio=0.8 model.num_leaves=50`
- DictConfig object passed to functions, dict unpacking with `**config.train`

### MLflow Tracking
- Local tracking: `mlflow.set_tracking_uri("file:///app/mlruns")`
- Param logging: model params + train params separately
- Artifact storage: local directory in mlruns/
- Table logging: DataFrames as JSON artifacts

### Streamlit App (`app/`)
- Sample notebooks in `app/streamlit_sample/` for reference
- Port 8501 exposed in compose.yml for web UI

## Project-Specific Patterns

### Multi-Step Time-Series Forecasting
- Not single-step ahead but 1-7 day ahead predictions
- Feature engineering creates multiple rows: one dataset row becomes 7 training rows
- Validation: `target_date = date + target_lead` enforced via dataframe_check
- Split happens before preprocessing to avoid data leakage

### Schema-First Development
- Schemas define contract between functions (input/output validation)
- Constraints documented in schema (e.g., weekday ∈ [0,6])
- Type hints use Pandera DataFrame types for IDE support
- Mismatch triggers clear error at runtime

### Local File-Based MLflow
- Not production setup (no tracking server)
- Useful for development and experiment comparison
- Artifacts and metrics stored locally in `mlruns/`

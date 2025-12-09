# Environment

This folder contains a minimal Python environment setup. If you haven't used the uv package manager yet, I highly recommend it!

## Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Using uv pip

```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

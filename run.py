"""Entry point for the Bug Report Accuracy Analyzer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from configs.config import config


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
    )

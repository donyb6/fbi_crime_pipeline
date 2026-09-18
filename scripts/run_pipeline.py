import os
import sys
import time
import importlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.logging_config import get_logger

logger = get_logger("run_pipeline")

PIPELINE_STEPS = [
    "extract_agencies",
    "extract_summarized",
    "silver_agencies",
    "silver_summarized",
    "gold_dim_offense",
    "gold_dim_state",
    "gold_dim_agency",
    "gold_offense_facts",
]


def run():
    logger.info("Pipeline run started")

    pipeline_start = time.time()

    for step_name in PIPELINE_STEPS:
        logger.info(f"Running: {step_name}")
        start = time.time()

        try:
            module = importlib.import_module(step_name)
            module.run()
        except Exception:
            logger.exception(f"Pipeline failed at step: {step_name}")
            raise

        elapsed = time.time() - start
        logger.info(f"Completed: {step_name} ({elapsed:.1f}s)")

    total_elapsed = time.time() - pipeline_start
    logger.info(f"Pipeline complete — all steps ran successfully in {total_elapsed:.1f}s")


if __name__ == "__main__":
    run()
from services.decision_pipeline import run_pipeline
import json

if __name__ == "__main__":
    result = run_pipeline()
    print(json.dumps(result, indent=4))

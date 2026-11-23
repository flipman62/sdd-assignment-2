import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate_spec


ROOT = Path(__file__).resolve().parents[1]


def main():
    schema = json.loads((ROOT / "system.schema.json").read_text())
    system = yaml.safe_load((ROOT / "system.yaml").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(system)

    for openapi_path in (
        ROOT / "services/habits/openapi.yaml",
        ROOT / "services/completions/openapi.yaml",
    ):
        spec = yaml.safe_load(openapi_path.read_text())
        validate_spec(spec)

    print("System and OpenAPI documents validated")


if __name__ == "__main__":
    main()

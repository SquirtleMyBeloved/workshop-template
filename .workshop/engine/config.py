import yaml
from pathlib import Path
import re

class WorkshopError(Exception):
    """Expected user or configuration error (bad YAML, missing file, etc.)."""

def load_config(config_path: Path) -> dict:
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        raise WorkshopError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as err:
        raise WorkshopError(f"Invalid YAML syntax in {config_path}:\n{err}")

    if not isinstance(data, dict):
        raise WorkshopError(f"{config_path} is empty or does not contain a YAML mapping.")

    return data

def validate_config(data: dict, repo_root: Path) -> dict:
    #Check metadata field
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise WorkshopError(f"Metadata section is missing or empty in configuration file")

    for metadata_field in ["title", "description"]:
        value = metadata.get(metadata_field)
        if not isinstance(value, str) or not value.strip():
            raise WorkshopError(f"'metadata.{metadata_field}' must be a non-empty string")

    #Check environment field
    environment = data.get("environment")
    if not isinstance(environment, dict):
        raise WorkshopError(f"Environment section is missing or empty in configuration file")

    template_name = environment.get("dockerfile_template")
    if not isinstance(template_name, str) or not template_name.strip():
        raise WorkshopError(f"'environment.dockerfile_template' must be a non-empty string")

    #Guard against path traversal
    if "/" in template_name or "\\" in template_name or ".." in template_name:
        raise WorkshopError(f"Invalid dockerfile_template name: '{template_name}'")

    template_path = repo_root / ".workshop" / "dockerfiles" / f"{template_name}.Dockerfile"
    if not template_path.is_file():
        raise WorkshopError(f"Dockerfile template '{template_name}' not found at: {template_path}")

    #Check exercises field
    exercises = data.get("exercises")
    if not isinstance(exercises, list) or len(exercises) == 0:
        raise WorkshopError(f"Exercises section is missing or empty in configuration file")

    seen_ids = set()

    for i, ex in enumerate(exercises, start=1):
        if not isinstance(ex, dict):
            raise WorkshopError(f"Exercise #{i} ({ex}) is missing or empty in configuration file")

        ex_id = ex.get("id")
        if not ex_id or not isinstance(ex_id, str):
            raise WorkshopError(f"Exercise #{i} is missing a valid 'id' field.")

        if not re.match(r"^[a-z0-9-]+$", ex_id):
            raise WorkshopError(f"Exercise #{i} id '{ex_id}' must contain only lowercase letters, numbers, and hyphens.")

        if ex_id in seen_ids:
            raise WorkshopError(f"Duplicate exercise id '{ex_id}' found at Exercise #{i}.")

        seen_ids.add(ex_id)

        if not ex.get("title"):
            raise WorkshopError(f"Exercise #{i} ('{ex_id}') is missing a 'title' field.")

    environment.setdefault("dependencies", {})
    environment["dependencies"].setdefault("apt", [])
    environment["dependencies"].setdefault("pip", [])
    environment.setdefault("linters", {})

    for ex in exercises:
        ex.setdefault("extra_dir", [])
        ex.setdefault("extra_files", [])
        ex.setdefault("exclude_common", [])

    return data

def get_config(config_path: Path) -> dict:
    repo_root = config_path.resolve().parent
    raw_data = load_config(config_path)
    return validate_config(raw_data, repo_root)

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    cfg = get_config(root / "workshop.yaml")
    print(f"OK: Loaded '{cfg['metadata']['title']}' ({len(cfg['exercises'])} exercises)")
    
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_milchik_backlog_is_json_serializable_after_yaml_load():
    """Hermes Kanban stores backlog mirror bodies as JSON.

    PyYAML converts unquoted ISO dates into datetime.date objects, which causes
    json.dumps() to fail inside sync_backlog_to_board. Persisted backlog values
    must therefore remain JSON-native after yaml.safe_load().
    """
    backlog = yaml.safe_load((ROOT / "agents/milchik/backlog.yaml").read_text())
    json.dumps(backlog)

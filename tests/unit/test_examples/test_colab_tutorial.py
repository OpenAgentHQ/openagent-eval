import json
from pathlib import Path

NOTEBOOK = (
    Path(__file__).parents[3] / "examples" / "openagent_eval_colab_tutorial.ipynb"
)


def _data_loading_cell_source() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell.get("id") == "a0e2944d":
            return "".join(cell["source"])
    raise AssertionError("data-loading cell not found")


def test_colab_data_loading_closes_json_file():
    source = _data_loading_cell_source()

    assert 'cases = json.load(open("data.json"))' not in source
    assert 'with open("data.json") as f:' in source
    assert "cases = json.load(f)" in source

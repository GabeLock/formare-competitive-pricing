from src.processing.matcher import build_item_hash


def test_hash_is_stable_for_sorted_specs():
    a = build_item_hash("c", "p", {"width_mm": 1000, "thickness_mm": 0.43})
    b = build_item_hash("c", "p", {"thickness_mm": 0.43, "width_mm": 1000})
    assert a == b


def test_hash_changes_with_specs():
    a = build_item_hash("c", "p", {"width_mm": 1000})
    b = build_item_hash("c", "p", {"width_mm": 1200})
    assert a != b


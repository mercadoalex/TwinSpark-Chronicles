from app.utils.beat_transformer import transform_beats


class TestTransformBeats:
    """Unit tests for transform_beats()."""

    def test_single_beat_all_fields(self):
        history = [
            {
                "narration": "The siblings entered the cave.",
                "child1_perspective": "Ale felt brave.",
                "child2_perspective": "Sofi was curious.",
                "scene_image_url": "https://img.example.com/scene1.png",
                "choiceMade": "Enter the cave",
                "choices": ["Enter the cave", "Go around"],
                "timestamp": 1700000000,
            }
        ]
        result = transform_beats(history)
        assert len(result) == 1
        beat = result[0]
        assert beat["narration"] == "The siblings entered the cave."
        assert beat["child1_perspective"] == "Ale felt brave."
        assert beat["child2_perspective"] == "Sofi was curious."
        assert beat["scene_image_url"] == "https://img.example.com/scene1.png"
        assert beat["choice_made"] == "Enter the cave"
        assert beat["available_choices"] == ["Enter the cave", "Go around"]
        assert "timestamp" not in beat
        assert "choiceMade" not in beat
        assert "choices" not in beat

    def test_multiple_beats(self):
        history = [
            {"narration": "Beat one.", "choiceMade": "A", "choices": ["A", "B"], "timestamp": 1},
            {"narration": "Beat two.", "choiceMade": "B", "choices": ["B", "C"], "timestamp": 2},
            {"narration": "Beat three.", "choiceMade": None, "choices": [], "timestamp": 3},
        ]
        result = transform_beats(history)
        assert len(result) == 3
        assert result[0]["narration"] == "Beat one."
        assert result[1]["choice_made"] == "B"
        assert result[2]["available_choices"] == []

    def test_missing_optional_fields_default(self):
        history = [{"narration": "Only narration here."}]
        result = transform_beats(history)
        beat = result[0]
        assert beat["narration"] == "Only narration here."
        assert beat["child1_perspective"] is None
        assert beat["child2_perspective"] is None
        assert beat["scene_image_url"] is None
        assert beat["choice_made"] is None
        assert beat["available_choices"] == []

    def test_timestamp_is_dropped(self):
        history = [
            {
                "narration": "Adventure begins.",
                "timestamp": 9999999999,
                "extra_field": "should also be dropped",
            }
        ]
        result = transform_beats(history)
        beat = result[0]
        assert "timestamp" not in beat
        assert "extra_field" not in beat
        # Only expected keys present
        expected_keys = {
            "narration", "child1_perspective", "child2_perspective",
            "scene_image_url", "choice_made", "available_choices",
        }
        assert set(beat.keys()) == expected_keys

    def test_empty_history(self):
        assert transform_beats([]) == []

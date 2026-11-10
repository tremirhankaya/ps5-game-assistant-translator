from ps5_translator.ocr.stability import StabilityFilter


def feed_all(f, texts):
    return [f.feed(t) for t in texts]


def test_text_is_sent_after_two_matching_reads_and_only_once():
    f = StabilityFilter()
    out = feed_all(f, ["Where is the key?"] * 4)
    assert out == [None, "Where is the key?", None, None]


def test_small_ocr_differences_count_as_the_same_subtitle():
    f = StabilityFilter()
    out = feed_all(f, ["Where is the key?", "Where is the kev?", "Where is the key?"])
    assert out[0] is None and out[1] is not None and out[2] is None


def test_typewriter_subtitles_wait_until_text_stops_growing():
    f = StabilityFilter()
    out = feed_all(f, ["We", "We need to", "We need to move. Now!", "We need to move. Now!"])
    assert out == [None, None, None, "We need to move. Now!"]


def test_new_subtitle_is_sent():
    f = StabilityFilter()
    out = feed_all(f, ["Let's go."] * 2 + ["Hold on. Did you hear that?"] * 2)
    assert out == [None, "Let's go.", None, "Hold on. Did you hear that?"]


def test_same_line_can_come_back_after_it_disappeared():
    f = StabilityFilter()
    out = feed_all(f, ["Let's go."] * 2 + [""] * 3 + ["Let's go."] * 2)
    assert out[1] == "Let's go." and out[-1] == "Let's go."


def test_brief_flicker_does_not_resend():
    f = StabilityFilter()
    out = feed_all(f, ["Let's go."] * 2 + [""] + ["Let's go."] * 2)
    assert out.count("Let's go.") == 1


def test_noise_is_ignored():
    f = StabilityFilter()
    assert feed_all(f, [".", "1", " - "]) == [None, None, None]


def test_confident_finished_sentence_is_sent_on_first_read():
    f = StabilityFilter()
    assert f.feed("Where is the key?", score=0.98) == "Where is the key?"
    assert f.sent_fast
    assert f.feed("Where is the key?", score=0.98) is None  # not sent twice


def test_fast_path_needs_confidence_and_sentence_end():
    f = StabilityFilter()
    assert f.feed("Where is the key?", score=0.80) is None
    assert f.feed("We need to", score=0.99) is None


def test_first_seen_time_is_kept_for_delay_measurement():
    f = StabilityFilter()
    f.feed("We need to go", when=10.0)
    assert f.feed("We need to go", when=10.4) == "We need to go"
    assert f.sent_first_seen == 10.0

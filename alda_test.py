#!/usr/bin/env python
import alda


def test_check_format():
    valid_values = ["assets", "dash", "download", "hls", "mp4", "ott",
                    "smooth", "videoads"]
    # Test valid values return True
    for value in valid_values:
        assert alda.check_format(value) is True
        print("Valid value got marked as False: " + value)
    # Test that invalid value returns False
    assert alda.check_format("foo") is False


def test_check_geo():
    valid_values = ["eu", "in", "jp", "row", "us"]
    # Test valid values return True
    for value in valid_values:
        assert alda.check_geo(value) is True
        print("Valid value got marked as False: " + value)
    # Test invalid value returns False
    assert alda.check_geo("foo") is False

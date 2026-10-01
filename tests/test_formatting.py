from eliude_cli.formatting import print_submission_result


def failed_sample(**fields):
    tc = {"id": 1, "is_sample": True, "passed": False, "reason": "wrong_answer"}
    tc.update(fields)
    return {"status": "failed", "result_detail": {"test_cases": [tc], "passed_count": 0, "total_count": 1}}


def test_failed_sample_shows_input_and_outputs_as_plain_lines(cli_config, capsys):
    print_submission_result(failed_sample(stdin_data="1\r\n2", expected_stdout="3\r\n", stdout="4\n", stderr=""))
    out = capsys.readouterr().out
    assert "\\r" not in out and "\\n" not in out and "'" not in out
    assert (
        "  Input:\n"
        "    1\n"
        "    2\n"
        "  Expected output:\n"
        "    3\n"
        "  Your output:\n"
        "    4\n"
    ) in out
    assert "stderr:" not in out
    assert "space at the end" not in out


def test_trailing_spaces_in_outputs_are_marked_with_a_legend(cli_config, capsys):
    print_submission_result(failed_sample(stdin_data="1 2", expected_stdout="3", stdout="3 \n"))
    out = capsys.readouterr().out
    assert "    3·\n" in out
    assert "(· = space at the end of a line, → = tab)" in out


def test_empty_output_is_shown_as_empty(cli_config, capsys):
    print_submission_result(failed_sample(stdin_data="", expected_stdout="3", stdout=""))
    out = capsys.readouterr().out
    assert "  Your output:\n    (empty)\n" in out


def test_stderr_is_shown_when_present(cli_config, capsys):
    print_submission_result(failed_sample(stdin_data="1", expected_stdout="1", stdout="", stderr="Segmentation fault\n"))
    assert "  stderr:\n    Segmentation fault\n" in capsys.readouterr().out


def test_hidden_test_case_shows_no_data(cli_config, capsys):
    data = failed_sample()
    data["result_detail"]["test_cases"][0]["is_sample"] = False
    print_submission_result(data)
    out = capsys.readouterr().out
    assert "Test case 1: FAIL (wrong_answer)" in out
    assert "Input:" not in out

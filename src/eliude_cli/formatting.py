import typer


def print_submission_result(data: dict) -> None:
    status = data["status"]

    if status == "compile_error":
        typer.secho("Compilation failed:", fg=typer.colors.RED, bold=True)
        typer.echo(data.get("compile_output", "").rstrip("\n"))
        return

    result = data.get("result_detail", {})
    test_cases = result.get("test_cases", [])
    for i, tc in enumerate(test_cases, start=1):
        label = f"Test case {i}"
        if tc.get("passed"):
            typer.secho(f"{label}: PASS", fg=typer.colors.GREEN)
        else:
            reason = tc.get("reason") or "failed"
            typer.secho(f"{label}: FAIL ({reason})", fg=typer.colors.RED)
            if tc.get("is_sample"):
                if "stdin_data" in tc:
                    typer.echo(f"  stdin:    {tc['stdin_data']!r}")
                if "expected_stdout" in tc:
                    typer.echo(f"  expected: {tc['expected_stdout']!r}")
                if "stdout" in tc:
                    typer.echo(f"  actual:   {tc['stdout']!r}")
                if tc.get("stderr"):
                    typer.echo(f"  stderr:   {tc['stderr']!r}")

    ai_check = result.get("ai_check")
    criteria_not_met = bool(ai_check) and not ai_check.get("criteria_met", True)
    if criteria_not_met:
        typer.secho("Criteria not met:", fg=typer.colors.RED, bold=True)
        typer.echo(f"  {ai_check.get('feedback', '')}")

    passed_count = result.get("passed_count", 0)
    total_count = result.get("total_count", 0)
    color = typer.colors.GREEN if status == "passed" else typer.colors.RED
    summary = f"Result: {passed_count}/{total_count} test cases passed"
    if criteria_not_met:
        summary += ", but criteria not met"
    typer.secho(summary, fg=color, bold=True)

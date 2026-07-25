from . import config

_MESSAGES = {
    "en": {
        # session.py
        "session.not_logged_in": "Not logged in. Run `eliude login` first.",
        "session.no_active_classroom": "No active classroom set. Run `eliude switch` first.",
        "session.no_active_practice": "No active practice set. Run `eliude practices switch` first.",
        # commands/submit.py
        "submit.grading": "Grading your submission...",
        # version_check.py
        "version.requires_newer": "This server requires eliude-cli {required}, but you have {installed} installed.",
        "version.requires_older": (
            "This server expects an older eliude-cli ({required}); you have {installed} installed."
        ),
        # formatting.py
        "submission.compilation_failed": "Compilation failed:",
        "submission.test_case_pass": "Test case {n}: PASS",
        "submission.test_case_fail": "Test case {n}: FAIL ({reason})",
        "submission.reason_failed": "failed",
        "submission.stdin_label": "stdin",
        "submission.expected_label": "expected",
        "submission.actual_label": "actual",
        "submission.stderr_label": "stderr",
        "submission.criteria_not_met": "Criteria not met:",
        "submission.result_summary": "Result: {passed}/{total} test cases passed",
        "submission.but_criteria_not_met": ", but criteria not met",
        # commands/config_cmd.py
        "config.base_url_set": "Base URL set to {url}",
        "config.language_set": "Language set to {language}",
        "config.unsupported_language": "Unsupported language '{language}'. Supported: {supported}",
        # commands/get.py
        "get.file_exists": "File '{target}' already exists.",
        "get.overwrite_prompt": "Overwrite it?",
        "get.enter_filename_prompt": "Enter a filename to save as instead",
        "get.saved": "Saved latest submission for '{slug}' to {target}.",
        # commands/practices.py
        "practices.none_yet": "This classroom has no practices yet.",
        "practices.timed_label": "timed {minutes}min",
        "practices.no_time_limit": "no time limit",
        "practices.not_found": "No practice '{slug}' in the active classroom.",
        "practices.using": "Using practice '{title}' ({slug}).",
        "practices.time_limit_ends": "Time limit: ends at {ends_at}",
        # commands/signup.py
        "signup.passwords_mismatch": "Passwords don't match.",
        "signup.welcome": "Welcome, {name}! Joined classroom '{classroom_name}' ({classroom_slug}).",
        # commands/login.py
        "login.logged_in_as": "Logged in as {username}.",
        "login.logged_out": "Logged out.",
        # commands/classrooms.py
        "classrooms.none_enrolled": "You are not enrolled in any classrooms yet.",
        "classrooms.not_enrolled_in": "You are not enrolled in classroom '{slug}'.",
        "classrooms.switched": "Switched to classroom '{name}' ({slug}).",
        # commands/questions.py
        "questions.no_questions": "No questions available.",
        "questions.last_submitted": "last submitted: {timestamp}",
        "questions.only_one_display_flag": (
            "Use only one of --caption, --input-sample, --output-sample at a time."
        ),
        "questions.no_sample": "No sample test case available.",
        "questions.no_sample_to_download": "No sample test case available to download.",
        "questions.difficulty_label": "Difficulty: {difficulty}",
        "questions.limits_label": "Time limit: {time}s  Memory limit: {memory}MB",
        "questions.tags_label": "Tags: {tags}",
        "questions.sample_test_cases_header": "Sample test cases:",
        "questions.input_label": "Input:    {value}",
        "questions.expected_label": "Expected: {value}",
        "questions.saved_sample": "Saved sample test case to {input_path} and {output_path}.",
        "questions.caption_classroom": "Classroom: {classroom}",
        "questions.caption_practice": "Practice: {practice}",
        "questions.caption_question": "Question: {slug}",
        # commands/status.py
        "status.server_unreachable": "Server: {url} — unreachable ({error})",
        "status.server_reachable": "Server: {url} (v{version}, reachable)",
        "status.questions_label": "Questions: {total}",
        "status.passed_label": "Passed: {passed}",
        "status.failed_label": "Failed: {failed}",
        "status.score_label": "Score: {score}% ({passed}/{total})",
        "status.logged_in_as": "Logged in as: {username}",
        "status.no_practices_yet": "No practices yet.",
        "status.classroom_label": "Classroom: {name} ({slug})",
        "status.practice_label": "Practice: {slug}",
    },
    "pt-BR": {
        # session.py
        "session.not_logged_in": "Você não está logado. Rode `eliude login` primeiro.",
        "session.no_active_classroom": "Nenhuma turma ativa. Rode `eliude switch` primeiro.",
        "session.no_active_practice": "Nenhuma practice ativa. Rode `eliude practices switch` primeiro.",
        # commands/submit.py
        "submit.grading": "Avaliando sua submissão...",
        # version_check.py
        "version.requires_newer": (
            "Este servidor requer o eliude-cli {required}, mas você tem o {installed} instalado."
        ),
        "version.requires_older": (
            "Este servidor espera uma versão mais antiga do eliude-cli ({required}); "
            "você tem o {installed} instalado."
        ),
        # formatting.py
        "submission.compilation_failed": "Falha na compilação:",
        "submission.test_case_pass": "Caso de teste {n}: PASSOU",
        "submission.test_case_fail": "Caso de teste {n}: FALHOU ({reason})",
        "submission.reason_failed": "falhou",
        "submission.stdin_label": "entrada",
        "submission.expected_label": "esperado",
        "submission.actual_label": "obtido",
        "submission.stderr_label": "stderr",
        "submission.criteria_not_met": "Critério não atendido:",
        "submission.result_summary": "Resultado: {passed}/{total} casos de teste passaram",
        "submission.but_criteria_not_met": ", mas o critério não foi atendido",
        # commands/config_cmd.py
        "config.base_url_set": "URL do servidor definida como {url}",
        "config.language_set": "Idioma definido como {language}",
        "config.unsupported_language": "Idioma '{language}' não suportado. Suportados: {supported}",
        # commands/get.py
        "get.file_exists": "O arquivo '{target}' já existe.",
        "get.overwrite_prompt": "Sobrescrever?",
        "get.enter_filename_prompt": "Digite um nome de arquivo alternativo para salvar",
        "get.saved": "Última submissão de '{slug}' salva em {target}.",
        # commands/practices.py
        "practices.none_yet": "Esta turma ainda não tem practices.",
        "practices.timed_label": "com tempo, {minutes}min",
        "practices.no_time_limit": "sem prazo",
        "practices.not_found": "Nenhuma practice '{slug}' na turma ativa.",
        "practices.using": "Usando a practice '{title}' ({slug}).",
        "practices.time_limit_ends": "Prazo: termina às {ends_at}",
        # commands/signup.py
        "signup.passwords_mismatch": "As senhas não coincidem.",
        "signup.welcome": "Bem-vindo(a), {name}! Você entrou na turma '{classroom_name}' ({classroom_slug}).",
        # commands/login.py
        "login.logged_in_as": "Logado como {username}.",
        "login.logged_out": "Sessão encerrada.",
        # commands/classrooms.py
        "classrooms.none_enrolled": "Você ainda não está matriculado em nenhuma turma.",
        "classrooms.not_enrolled_in": "Você não está matriculado na turma '{slug}'.",
        "classrooms.switched": "Trocado para a turma '{name}' ({slug}).",
        # commands/questions.py
        "questions.no_questions": "Nenhuma questão disponível.",
        "questions.last_submitted": "última submissão: {timestamp}",
        "questions.only_one_display_flag": (
            "Use apenas uma opção por vez entre --caption, --input-sample e --output-sample."
        ),
        "questions.no_sample": "Nenhum caso de teste de amostra disponível.",
        "questions.no_sample_to_download": "Nenhum caso de teste de amostra disponível para baixar.",
        "questions.difficulty_label": "Dificuldade: {difficulty}",
        "questions.limits_label": "Tempo limite: {time}s  Memória limite: {memory}MB",
        "questions.tags_label": "Tags: {tags}",
        "questions.sample_test_cases_header": "Casos de teste de amostra:",
        "questions.input_label": "Entrada: {value}",
        "questions.expected_label": "Esperado: {value}",
        "questions.saved_sample": "Caso de teste de amostra salvo em {input_path} e {output_path}.",
        "questions.caption_classroom": "Turma: {classroom}",
        "questions.caption_practice": "Practice: {practice}",
        "questions.caption_question": "Questão: {slug}",
        # commands/status.py
        "status.server_unreachable": "Servidor: {url} — inacessível ({error})",
        "status.server_reachable": "Servidor: {url} (v{version}, acessível)",
        "status.questions_label": "Questões: {total}",
        "status.passed_label": "Aprovadas: {passed}",
        "status.failed_label": "Reprovadas: {failed}",
        "status.score_label": "Nota: {score}% ({passed}/{total})",
        "status.logged_in_as": "Logado como: {username}",
        "status.no_practices_yet": "Nenhuma practice ainda.",
        "status.classroom_label": "Turma: {name} ({slug})",
        "status.practice_label": "Practice: {slug}",
    },
}


def t(key: str, **kwargs) -> str:
    language = config.get_language()
    template = _MESSAGES.get(language, {}).get(key)
    if template is None:
        template = _MESSAGES["en"].get(key, key)
    return template.format(**kwargs) if kwargs else template

from . import config

_MESSAGES = {
    "en": {
        # client.py
        "api.unreachable": "Could not reach the Eliude server at {url}.",
        "api.timeout": "The Eliude server at {url} took too long to respond. Try again in a moment.",
        "api.request_failed": "Could not complete the request to the Eliude server at {url}.",
        "api.redirected": (
            "The server moved to a new address and this request can't follow it. "
            "Run: eliude config set-url {url}"
        ),
        "api.not_logged_in": "Not logged in or token expired. Run `eliude login`.",
        "api.not_found": "Not found.",
        "api.rate_limited": "Too many requests. Wait a moment and try again.",
        "api.server_error": (
            "The Eliude server ran into an error (HTTP {status}). Try again in a moment; "
            "if it keeps happening, let your teacher know."
        ),
        "api.unexpected_status": "Unexpected response from the Eliude server (HTTP {status}).",
        # main.py
        "error.unexpected": (
            "Something went wrong and eliude couldn't finish this command. "
            "If it keeps happening, let your teacher know. "
            "(Run with ELIUDE_DEBUG=1 to see the technical details.)"
        ),
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
        "submission.stdin_label": "Input:",
        "submission.expected_label": "Expected output:",
        "submission.actual_label": "Your output:",
        "submission.stderr_label": "stderr:",
        "submission.trailing_space_legend": "(· = space at the end of a line, → = tab)",
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
        "practices.choose": "Choose a practice:",
        "practices.window_upcoming": "not open yet",
        "practices.window_closed": "closed",
        "practices.none_open": "No practice in this classroom is open right now.",
        "practices.confirm_start_timed": (
            "'{title}' is timed ({minutes} min) and the clock starts as soon as you select it. Start now?"
        ),
        # commands/signup.py
        "signup.passwords_mismatch": "Passwords don't match.",
        "signup.welcome": "Welcome, {name}! Joined classroom '{classroom_name}' ({classroom_slug}).",
        # commands/login.py
        "login.logged_in_as": "Logged in as {username}.",
        "login.logged_out": "Logged out.",
        # commands/change_password.py
        "change_password.mismatch": "Passwords don't match.",
        "change_password.success": "Password changed.",
        # commands/classrooms.py
        "classrooms.none_enrolled": "You are not enrolled in any classrooms yet.",
        "classrooms.not_enrolled_in": "You are not enrolled in classroom '{slug}'.",
        "classrooms.switched": "Switched to classroom '{name}' ({slug}).",
        "classrooms.choose": "Choose a classroom:",
        # prompts.py
        "prompt.select_instruction": "(arrow keys or number, then Enter)",
        "prompt.select_instruction_arrows": "(arrow keys, then Enter)",
        "prompt.current": "(current)",
        "prompt.cancelled": "Cancelled.",
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
        "questions.sample_n": "Example {n}",
        "questions.input_header": "Input:",
        "questions.expected_header": "Expected output:",
        "questions.empty_value": "(empty)",
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
        # main.py — help text (group/command descriptions, --version)
        "help.root": "CLI for the Eliude C programming judge",
        "help.group.classrooms": "Manage your classrooms",
        "help.group.practices": "Manage practices in the active classroom",
        "help.group.questions": "Browse the active practice's questions",
        "help.group.submissions": "Check submission results",
        "help.group.config": "CLI configuration",
        "help.opt.version": "Show the version and exit.",
        "help.cmd.login": "Log in and store an auth token locally.",
        "help.cmd.logout": "Clear the locally stored auth token.",
        "help.cmd.change_password": "Set a new password — required if you're still on a temporary one your teacher set.",
        "help.cmd.signup": "Self-register as a student using a classroom join code, and log in.",
        "help.cmd.submit": "Submit a C solution for a question in the active practice.",
        "help.cmd.switch": (
            "Choose the active classroom and then practice from menus; a classroom slug skips the first menu."
        ),
        "help.cmd.get": "Show your latest submission for a question in the active practice.",
        "help.cmd.status": "Show your login, active classroom/practice, and question stats.",
        "help.cmd.show": "Show a question's statement and sample test cases.",
        "help.cmd.classrooms_list": "List the classrooms you belong to, marking the active one.",
        "help.cmd.practices_list": "List the practices available in the active classroom, marking the active one.",
        "help.cmd.practices_switch": (
            "Choose the active practice from a menu, or switch directly to a practice slug."
        ),
        "help.cmd.questions_list": "List the active practice's questions.",
        "help.cmd.submissions_status": "Check the status/result of a previous submission.",
        "help.cmd.config_set_url": "Point the CLI at a different Eliude backend.",
        "help.cmd.config_set_language": "Set the language eliude's messages are shown in.",
        # commands/get.py — option help
        "help.opt.get_save": "Save to <slug>.c instead of printing to stdout",
        "help.opt.get_overwrite": "With --save, overwrite the destination file without prompting",
        # commands/questions.py — option/argument help
        "help.opt.questions_show_timestamp": "Also show when you last submitted each question",
        "help.opt.questions_unsolved": "Only show questions you haven't passed yet (never submitted or failing)",
        "help.opt.questions_tag": "Only show questions with this tag (e.g. vetores)",
        "help.opt.show_download": (
            "Also save the first sample test case as <slug>_input.txt / <slug>_output.txt"
        ),
        "help.opt.show_caption": "Show only the title/statement, formatted as a C comment block",
        "help.opt.show_input_sample": "Show only the first sample test case's input",
        "help.opt.show_output_sample": "Show only the first sample test case's expected output",
        # commands/practices.py — argument help
        "help.arg.practices_switch_slug": "Practice slug to switch to",
        # commands/classrooms.py — argument help
        "help.arg.classrooms_switch_slug": "Classroom slug to switch to",
        # commands/status.py — option help
        "help.opt.status_all": "Show stats for every practice in every classroom you belong to",
        # commands/config_cmd.py — argument help
        "help.arg.config_set_language": "Language code, e.g. en or pt-BR",
    },
    "pt-BR": {
        # client.py
        "api.unreachable": "Não foi possível conectar ao servidor Eliude em {url}.",
        "api.timeout": "O servidor Eliude em {url} demorou demais para responder. Tente de novo em instantes.",
        "api.request_failed": "Não foi possível concluir a requisição ao servidor Eliude em {url}.",
        "api.redirected": (
            "O servidor mudou de endereço e esta requisição não consegue segui-lo. "
            "Rode: eliude config set-url {url}"
        ),
        "api.not_logged_in": "Você não está logado ou o token expirou. Rode `eliude login`.",
        "api.not_found": "Não encontrado.",
        "api.rate_limited": "Muitas requisições seguidas. Aguarde um pouco e tente de novo.",
        "api.server_error": (
            "O servidor Eliude encontrou um erro (HTTP {status}). Tente de novo em instantes; "
            "se continuar acontecendo, avise seu professor."
        ),
        "api.unexpected_status": "Resposta inesperada do servidor Eliude (HTTP {status}).",
        # main.py
        "error.unexpected": (
            "Algo deu errado e o eliude não conseguiu concluir este comando. "
            "Se continuar acontecendo, avise seu professor. "
            "(Rode com ELIUDE_DEBUG=1 para ver os detalhes técnicos.)"
        ),
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
        "submission.stdin_label": "Entrada:",
        "submission.expected_label": "Saída esperada:",
        "submission.actual_label": "Sua saída:",
        "submission.stderr_label": "stderr:",
        "submission.trailing_space_legend": "(· = espaço no fim da linha, → = tab)",
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
        "practices.choose": "Escolha a practice:",
        "practices.window_upcoming": "ainda não abriu",
        "practices.window_closed": "encerrada",
        "practices.none_open": "Nenhuma practice desta turma está aberta agora.",
        "practices.confirm_start_timed": (
            "'{title}' tem tempo ({minutes} min) e o cronômetro começa assim que você selecionar. Começar agora?"
        ),
        # commands/signup.py
        "signup.passwords_mismatch": "As senhas não coincidem.",
        "signup.welcome": "Bem-vindo(a), {name}! Você entrou na turma '{classroom_name}' ({classroom_slug}).",
        # commands/login.py
        "login.logged_in_as": "Logado como {username}.",
        "login.logged_out": "Sessão encerrada.",
        # commands/change_password.py
        "change_password.mismatch": "As senhas não coincidem.",
        "change_password.success": "Senha alterada.",
        # commands/classrooms.py
        "classrooms.none_enrolled": "Você ainda não está matriculado em nenhuma turma.",
        "classrooms.not_enrolled_in": "Você não está matriculado na turma '{slug}'.",
        "classrooms.switched": "Trocado para a turma '{name}' ({slug}).",
        "classrooms.choose": "Escolha a turma:",
        # prompts.py
        "prompt.select_instruction": "(setas ou número, depois Enter)",
        "prompt.select_instruction_arrows": "(setas, depois Enter)",
        "prompt.current": "(atual)",
        "prompt.cancelled": "Cancelado.",
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
        "questions.sample_n": "Exemplo {n}",
        "questions.input_header": "Entrada:",
        "questions.expected_header": "Saída esperada:",
        "questions.empty_value": "(vazia)",
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
        # main.py — help text (group/command descriptions, --version)
        "help.root": "CLI para o corretor de exercícios de C Eliude",
        "help.group.classrooms": "Gerencie suas turmas",
        "help.group.practices": "Gerencie as practices da turma ativa",
        "help.group.questions": "Navegue pelas questões da practice ativa",
        "help.group.submissions": "Consulte o resultado de submissões",
        "help.group.config": "Configuração do CLI",
        "help.opt.version": "Mostra a versão e sai.",
        "help.cmd.login": "Faz login e salva um token de autenticação localmente.",
        "help.cmd.logout": "Apaga o token de autenticação salvo localmente.",
        "help.cmd.change_password": "Define uma nova senha — obrigatório se você ainda está com a senha temporária que seu professor definiu.",
        "help.cmd.signup": "Auto-cadastro de aluno usando o código de uma turma, e já faz login.",
        "help.cmd.submit": "Envia uma solução em C para uma questão da practice ativa.",
        "help.cmd.switch": (
            "Escolhe a turma e depois a practice ativas em menus; informar o slug da turma pula o primeiro menu."
        ),
        "help.cmd.get": "Mostra sua última submissão de uma questão na practice ativa.",
        "help.cmd.status": "Mostra login, turma/practice ativa e estatísticas das questões.",
        "help.cmd.show": "Mostra o enunciado e os casos de teste de amostra de uma questão.",
        "help.cmd.classrooms_list": "Lista as turmas em que você está matriculado, marcando a ativa.",
        "help.cmd.practices_list": "Lista as practices disponíveis na turma ativa, marcando a ativa.",
        "help.cmd.practices_switch": (
            "Escolhe a practice ativa num menu, ou troca direto para o slug de uma practice."
        ),
        "help.cmd.questions_list": "Lista as questões da practice ativa.",
        "help.cmd.submissions_status": "Consulta o status/resultado de uma submissão anterior.",
        "help.cmd.config_set_url": "Aponta o CLI para um backend Eliude diferente.",
        "help.cmd.config_set_language": "Define o idioma em que as mensagens do eliude são mostradas.",
        # commands/get.py — option help
        "help.opt.get_save": "Salva em <slug>.c em vez de mostrar no terminal",
        "help.opt.get_overwrite": "Com --save, sobrescreve o arquivo de destino sem perguntar",
        # commands/questions.py — option/argument help
        "help.opt.questions_show_timestamp": "Também mostra quando você submeteu cada questão pela última vez",
        "help.opt.questions_unsolved": "Mostra só questões que você ainda não passou (nunca enviada ou reprovada)",
        "help.opt.questions_tag": "Mostra só questões com essa tag (ex. vetores)",
        "help.opt.show_download": (
            "Também salva o primeiro caso de teste de amostra como <slug>_input.txt / <slug>_output.txt"
        ),
        "help.opt.show_caption": "Mostra só o título/enunciado, formatado como um comentário de bloco C",
        "help.opt.show_input_sample": "Mostra só o input do primeiro caso de teste de amostra",
        "help.opt.show_output_sample": "Mostra só a saída esperada do primeiro caso de teste de amostra",
        # commands/practices.py — argument help
        "help.arg.practices_switch_slug": "Slug da practice para trocar",
        # commands/classrooms.py — argument help
        "help.arg.classrooms_switch_slug": "Slug da turma para trocar",
        # commands/status.py — option help
        "help.opt.status_all": "Mostra estatísticas de cada practice em cada turma em que você está matriculado",
        # commands/config_cmd.py — argument help
        "help.arg.config_set_language": "Código do idioma, ex. en ou pt-BR",
    },
}


def t(key: str, **kwargs) -> str:
    language = config.get_language()
    template = _MESSAGES.get(language, {}).get(key)
    if template is None:
        template = _MESSAGES["en"].get(key, key)
    return template.format(**kwargs) if kwargs else template

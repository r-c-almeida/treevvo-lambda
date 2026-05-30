"""
Cliente para a API de chat da OpenAI (ChatGPT).

A classe é configurável por instância: chave, instruções de sistema, modelo e SSL
não dependem de estado global. Cada instância pode usar `api_key` explícita,
variável de ambiente distinta (`api_key_env`) ou arquivo (`api_key_file`).

Arquivos de instrução de sistema ficam em ``docs/instructions/``. Use
``ChatGPTChat.from_instruction_file("nome")`` para instanciar a partir do nome
do arquivo (ex.: ``"roteiro"`` → ``docs/instructions/roteiro.txt``).

Ordem de resolução da chave: `api_key` → `api_key_file` → variável `api_key_env`.
"""

from __future__ import annotations

import inspect
import logging
import os
from pathlib import Path
from typing import Any

from source.env_util import try_load_dotenv
from source.logging_setup import log_text_limit, setup_logging

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"

# SSL (redes corporativas com proxy/inspeção HTTPS)
DEFAULT_SSL_VERIFY = False
DEFAULT_SSL_CA_BUNDLE = ""

# Raiz do repositório: .../source/llms/chatgpt_chat.py → parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Instruções de sistema por arquivo: docs/instructions/<nome>.txt
DEFAULT_INSTRUCTIONS_DIR = _PROJECT_ROOT / "docs" / "instructions"


def _normalize_instruction_filename(name: str) -> str:
    raw = (name or "").strip()
    if not raw:
        raise ValueError("O nome do arquivo de instrução não pode ser vazio.")
    p = Path(raw)
    if len(p.parts) != 1:
        raise ValueError(
            "Passe apenas o nome do arquivo (ex.: 'roteiro' ou 'roteiro.txt'), sem pastas."
        )
    fname = p.name
    if not Path(fname).suffix:
        fname = f"{fname}.txt"
    return fname


def resolve_instruction_path(
    name: str,
    *,
    instructions_dir: Path | None = None,
) -> Path:
    """
    Resolve o caminho absoluto para um arquivo em ``docs/instructions`` (ou ``instructions_dir``).

    Aceita só o nome do arquivo (ex.: ``"roteiro"`` ou ``"roteiro.txt"``). Sem ``..`` ou caminhos.
    """
    base = (instructions_dir or DEFAULT_INSTRUCTIONS_DIR).resolve()
    fname = _normalize_instruction_filename(name)
    out = (base / fname).resolve()
    try:
        out.relative_to(base)
    except ValueError as e:
        raise ValueError("Caminho de instrução inválido.") from e
    return out


def load_system_instructions_file(path: Path | str) -> str:
    """Lê texto UTF-8; ignora linhas vazias e linhas que começam com #."""
    p = Path(path)
    if not p.is_file():
        return ""
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def resolve_api_key(
    *,
    api_key: str | None = None,
    api_key_env: str | None = DEFAULT_API_KEY_ENV,
    api_key_file: Path | str | None = None,
) -> str:
    """Resolve a chave: explícita, depois arquivo, depois variável de ambiente."""
    if (api_key or "").strip():
        return api_key.strip()
    if api_key_file is not None:
        p = Path(api_key_file)
        if p.is_file():
            try:
                t = p.read_text(encoding="utf-8").strip()
                if t:
                    return t
            except OSError:
                pass
    if api_key_env:
        env = (os.environ.get(api_key_env) or "").strip()
        if env:
            return env
    return ""


def _truncate_for_log(text: str, limit: int | None = None) -> str:
    lim = log_text_limit() if limit is None else limit
    if lim <= 0 or len(text) <= lim:
        return text
    return text[:lim] + f"\n...[truncado no log, total_chars={len(text)}]"


def infer_external_caller() -> str:
    """Primeiro frame em ``source.*`` fora deste módulo (fallback se ``caller`` não for passado)."""
    for fr in inspect.stack()[1:]:
        mod = inspect.getmodule(fr.frame)
        name = mod.__name__ if mod else ""
        if name == __name__:
            continue
        if name.startswith("source."):
            return f"{name}.{fr.function}"
    return "unknown"


class ChatGPTChat:
    """Envia prompts ao modelo via API OpenAI; configuração isolada por instância."""

    @classmethod
    def from_instruction_file(
        cls,
        name: str,
        *,
        instructions_dir: Path | None = None,
        **kwargs: Any,
    ) -> ChatGPTChat:
        """
        Instancia o cliente usando um arquivo em ``docs/instructions`` pelo nome.

        Ex.: ``ChatGPTChat.from_instruction_file("roteiro")`` lê ``docs/instructions/roteiro.txt``.
        """
        path = resolve_instruction_path(name, instructions_dir=instructions_dir)
        if not path.is_file():
            logger.error(
                "from_instruction_file: instrução não encontrada name=%r path=%s",
                name,
                path,
            )
            raise FileNotFoundError(f"Arquivo de instrução não encontrado: {path}")
        kw = dict(kwargs)
        if "log_label" not in kw:
            kw["log_label"] = f"instructions:{path.name}"
        return cls(system_instructions_file=path, **kw)

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = DEFAULT_MODEL,
        system_instructions: str = "",
        system_instructions_file: Path | str | None = None,
        api_key_env: str | None = DEFAULT_API_KEY_ENV,
        api_key_file: Path | str | None = None,
        env_file: Path | str | None = None,
        ssl_verify: bool | None = None,
        ssl_ca_bundle: str | None = None,
        base_url: str | None = None,
        openai_client_kwargs: dict[str, Any] | None = None,
        log_label: str | None = None,
    ) -> None:
        setup_logging()
        if env_file is not None:
            try_load_dotenv(Path(env_file))

        key = resolve_api_key(
            api_key=api_key,
            api_key_env=api_key_env,
            api_key_file=api_key_file,
        )
        if not key:
            logger.error(
                "ChatGPTChat falha na criação: chave de API ausente (api_key_env=%r)",
                api_key_env,
            )
            raise ValueError(
                "Defina a chave: passe api_key, api_key_file, "
                f"ou a variável de ambiente {api_key_env!r} (ou ajuste api_key_env)."
            )

        self._model = model
        sys_text = (system_instructions or "").strip()
        if system_instructions_file is not None:
            from_file = load_system_instructions_file(system_instructions_file)
            if sys_text:
                self._system_instructions = f"{from_file}\n\n{sys_text}".strip()
            else:
                self._system_instructions = from_file
        else:
            self._system_instructions = sys_text

        self._log_label = log_label or (
            Path(system_instructions_file).name
            if system_instructions_file is not None
            else ("inline_system" if self._system_instructions.strip() else "no_system")
        )

        from openai import OpenAI

        http_client = _make_http_client_for_init(
            ssl_verify=ssl_verify,
            ssl_ca_bundle=ssl_ca_bundle,
        )
        kwargs: dict[str, Any] = dict(openai_client_kwargs or {})
        kwargs["api_key"] = key
        if http_client is not None:
            kwargs["http_client"] = http_client
        if base_url is not None:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)

        bu = str(base_url) if base_url else "default"
        logger.info(
            "ChatGPTChat criado model=%s log_label=%s api_key_env=%s base_url=%s "
            "system_instruction_chars=%d",
            self._model,
            self._log_label,
            api_key_env,
            bu,
            len(self._system_instructions or ""),
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def system_instructions(self) -> str:
        return self._system_instructions

    def send_prompt(self, prompt: str, *, caller: str | None = None) -> str:
        """
        Envia um único prompt como mensagem de usuário e devolve o texto da resposta.

        ``caller`` identifica quem chamou (ex.: ``HotelAgent``); se omitido, infere pela stack.
        """
        setup_logging()
        who = caller or infer_external_caller()
        text = (prompt or "").strip()
        if not text:
            logger.error("send_prompt rejeitado: prompt vazio caller=%s", who)
            raise ValueError("O prompt não pode ser vazio.")

        logger.info(
            "ChatGPT envio caller=%s model=%s log_label=%s user_prompt_chars=%d prompt=%s",
            who,
            self._model,
            self._log_label,
            len(text),
            _truncate_for_log(text),
        )

        messages: list[dict[str, str]] = []
        if self._system_instructions:
            messages.append({"role": "system", "content": self._system_instructions})
        messages.append({"role": "user", "content": text})

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=16_000,
            )
        except Exception:
            logger.exception(
                "ChatGPT erro na API caller=%s model=%s log_label=%s",
                who,
                self._model,
                self._log_label,
            )
            raise

        choice = response.choices[0]
        if choice.finish_reason == "length":
            logger.error(
                "ChatGPT resposta truncada caller=%s model=%s — aumente max_tokens ou reduza o prompt",
                who,
                self._model,
            )
            raise ValueError(
                f"Resposta do modelo truncada (finish_reason=length). "
                "Reduza o número de dias ou aumente max_tokens."
            )
        content = choice.message.content
        out = "" if content is None else content
        logger.info(
            "ChatGPT retorno caller=%s model=%s log_label=%s response_chars=%d response=%s",
            who,
            self._model,
            self._log_label,
            len(out),
            _truncate_for_log(out),
        )
        return out


def _make_http_client_for_init(
    *,
    ssl_verify: bool | None,
    ssl_ca_bundle: str | None,
):
    """Monta httpx.Client; parâmetros do construtor substituem os defaults do módulo."""
    import httpx

    ca = (ssl_ca_bundle if ssl_ca_bundle is not None else DEFAULT_SSL_CA_BUNDLE) or ""
    ca = ca.strip()
    if ca:
        path = Path(ca)
        if not path.is_file():
            raise ValueError(f"ssl_ca_bundle não é um arquivo válido: {ca}")
        return httpx.Client(verify=str(path.resolve()))

    verify = DEFAULT_SSL_VERIFY if ssl_verify is None else ssl_verify
    if not verify:
        return httpx.Client(verify=False)
    return None

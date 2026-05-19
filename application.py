"""
Aplicação principal: lê transcrições locais, orquestra agentes via RouterService
e grava o roteiro em Generated_Trips/<Cidade>/<cidade>_<dias>_<data>_<hora>.txt.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from source.logging_setup import setup_logging
from source.services.router_service import OnAgentComplete, RouterService
from source.agents.trip_types import PipelineResult, TripInput

logger = logging.getLogger(__name__)

# Diretório onde estão os .txt de transcrição (padrão: pasta deste arquivo)
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR

load_dotenv(PROJECT_ROOT / ".env")
setup_logging()

# Padrão de nomes dos arquivos de transcrição (ex.: transcricao_01.txt, transcricao_v=....txt)
TRANSCRIPT_GLOB = "transcricao*.txt"

# Roteiros gerados: pasta na raiz do projeto
GENERATED_TRIPS_DIR = PROJECT_ROOT / "Generated_Trips"


def safe_folder_name(raw: str) -> str:
    """Nome de pasta seguro no Windows e consistente com a UI web."""
    name = raw.strip()
    if not name:
        raise ValueError("Informe o nome da pasta.")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.replace("..", "_").strip()
    if not name or name in {".", ".."}:
        raise ValueError("Nome de pasta inválido.")
    return name


def build_generated_trip_output_path(city: str, days: int, *, when: datetime | None = None) -> Path:
    """
    ``Generated_Trips/<Cidade>/<cidade>_<dias>_<YYYY-MM-DD>_<HHMMSS>.txt``

    ``cidade`` na pasta e no prefixo do arquivo usa o mesmo nome sanitizado (Windows-safe).
    """
    safe = safe_folder_name(city)
    dt = when or datetime.now()
    date_s = dt.strftime("%Y-%m-%d")
    time_s = dt.strftime("%H%M%S")
    fname = f"{safe}_{int(days)}_{date_s}_{time_s}.txt"
    return GENERATED_TRIPS_DIR / safe / fname


class Application:
    """Orquestra leitura das transcrições, pipeline de agentes e gravação da resposta."""

    def __init__(
        self,
        base_dir: Path | None = None,
        transcript_glob: str = TRANSCRIPT_GLOB,
    ) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else BASE_DIR
        self.transcript_glob = transcript_glob

    def list_transcript_files(self) -> list[Path]:
        paths = sorted(self.base_dir.glob(self.transcript_glob))
        return [p for p in paths if p.is_file()]

    def build_transcripts_block(self, paths: list[Path]) -> str:
        chunks: list[str] = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            chunks.append(f"=== ARQUIVO: {path.name} ===\n")
            chunks.append(text.rstrip())
            chunks.append("\n\n")
        return "".join(chunks).strip()

    def basic_validation(self, city: str, days: int, _dates_note: str) -> None:
        city_clean = (city or "").strip()
        if not city_clean:
            raise ValueError("Informe o nome da cidade.")
        if days < 1:
            raise ValueError("A quantidade de dias deve ser >= 1.")

    def run(
        self,
        city: str,
        days: int,
        dates_note: str = "",
        *,
        complementary_info: str = "",
        router: RouterService | None = None,
        on_agent_complete: OnAgentComplete | None = None,
    ) -> tuple[Path, PipelineResult]:
        """
        Executa o pipeline configurado em ``RouterService`` (ou instância passada em ``router``).

        ``days`` costuma ser derivado do intervalo de datas; ``dates_note`` descreve o período;
        ``complementary_info`` é texto livre com preferências adicionais.
        Retorna o caminho do arquivo gravado e o resultado completo do pipeline.
        """
        self.basic_validation(city, days, dates_note)
        city_clean = (city or "").strip()
        dates_clean = (dates_note or "").strip()
        comp_clean = (complementary_info or "").strip()

        logger.info(
            "Application.run início base_dir=%s glob=%s city=%r days=%s dates_note=%r complementary_info=%r",
            self.base_dir,
            self.transcript_glob,
            city_clean,
            int(days),
            dates_clean,
            comp_clean,
        )

        paths = self.list_transcript_files()
        if not paths:
            logger.error(
                "Application.run falha: nenhum arquivo matching %s em %s",
                self.transcript_glob,
                self.base_dir,
            )


        transcripts_block = self.build_transcripts_block(paths)
        logger.info(
            "Application.run transcrições: %d arquivo(s), bloco_chars=%d",
            len(paths),
            len(transcripts_block),
        )

        trip = TripInput(
            city=city_clean,
            days=int(days),
            dates_note=dates_clean,
            complementary_info=comp_clean,
        )

        pipeline = router if router is not None else RouterService()
        try:
            result = pipeline.run(
                trip,
                transcripts_block,
                on_agent_complete=on_agent_complete,
            )
        except Exception:
            logger.exception(
                "Application.run falhou após pipeline city=%r days=%s",
                city_clean,
                int(days),
            )
            raise

        response_path = build_generated_trip_output_path(city_clean, int(days))
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_text(result.final_text, encoding="utf-8")
        logger.info(
            "Application.run sucesso response_path=%s final_chars=%d meta=%s",
            response_path,
            len(result.final_text or ""),
            result.meta,
        )
        return response_path, result


def main() -> None:
    out, _ = Application().run(city="Londres", days=3, dates_note="Novembro")
    print(f"Resposta salva em: {out}")


if __name__ == "__main__":
    main()

"""Agente de mapas a partir do roteiro já montado."""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class MapsAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("maps.txt")

    def run(
        self,
        city: str,
        days: int,
        complementary_info: str,
        route_plan: str,
    ) -> str:
        return self._timed_chat(
            self._build_prompt(
                city=city,
                days=days,
                complementary_info=complementary_info,
                route_plan=(route_plan or "").strip()
                or "(vazio — execute a roteirização antes)",
            )
        )

    def _build_prompt(
        self,
        city: str,
        days: int,
        complementary_info: str,
        route_plan: str,
    ) -> str:
        return f"""\
Cidade: {city}

--- Roteiro ---
{route_plan}
"""

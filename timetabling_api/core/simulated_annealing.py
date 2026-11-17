"""Simulated Annealing para refinamento local de conflitos e redução de janelas vagas."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Sequence

from .avaliador import avaliar_solucao, identificar_aulas_em_conflito
from .dominio import ContextoExecucao, MetricasAvaliacao

AvaliadorFn = Callable[[Sequence[int], ContextoExecucao], MetricasAvaliacao]


@dataclass(frozen=True)
class ConfiguracaoSA:
    """Parâmetros de resfriamento e vizinhança do Simulated Annealing."""

    temperatura_inicial: float = 400.0
    temperatura_final: float = 0.5
    taxa_resfriamento: float = 0.985
    iteracoes_por_temperatura: int = 12
    probabilidade_troca: float = 0.35


def executar_simulated_annealing(
    cromossomo_inicial: Sequence[int],
    contexto: ContextoExecucao,
    config: ConfiguracaoSA = ConfiguracaoSA(),
    rng: random.Random | None = None,
    avaliador: AvaliadorFn = avaliar_solucao,
) -> tuple[list[int], MetricasAvaliacao, list[float]]:
    """Refina uma solução inicial via recozimento simulado e retorna a melhor solução encontrada."""
    gerador = rng or random.Random()

    atual = list(cromossomo_inicial)
    metrica_atual = avaliar_solucao_atual = avaliador(atual, contexto)

    melhor = list(atual)
    melhor_metrica = avaliar_solucao_atual
    historico: list[float] = [melhor_metrica.custo_total]

    if melhor_metrica.custo_total == 0 or len(atual) == 0:
        return melhor, melhor_metrica, historico

    temperatura = config.temperatura_inicial
    while temperatura > config.temperatura_final and melhor_metrica.custo_total > 0:
        for _ in range(config.iteracoes_por_temperatura):
            conflitantes = (
                identificar_aulas_em_conflito(atual, contexto)
                if metrica_atual.violacoes_fortes > 0
                else []
            )
            movimento = _gerar_vizinho(
                atual, contexto, config.probabilidade_troca, conflitantes, gerador
            )
            if movimento is None:
                continue

            _aplicar_movimento(atual, movimento)
            metrica_vizinho = avaliador(atual, contexto)
            delta = metrica_vizinho.custo_total - metrica_atual.custo_total

            if delta <= 0 or gerador.random() < math.exp(-delta / temperatura):
                metrica_atual = metrica_vizinho
                if metrica_atual.custo_total < melhor_metrica.custo_total:
                    melhor = list(atual)
                    melhor_metrica = metrica_atual
                    if melhor_metrica.custo_total == 0:
                        break
            else:
                _reverter_movimento(atual, movimento)

        historico.append(melhor_metrica.custo_total)
        temperatura *= config.taxa_resfriamento

    return melhor, melhor_metrica, historico


def _gerar_vizinho(
    cromossomo: Sequence[int],
    contexto: ContextoExecucao,
    probabilidade_troca: float,
    conflitantes: Sequence[int],
    rng: random.Random,
) -> tuple[str, int, int, int, int] | None:
    """Propõe uma alteração de slot único ou uma troca válida entre duas aulas."""
    qtd_aulas = len(cromossomo)
    if qtd_aulas >= 2 and rng.random() < probabilidade_troca:
        for _ in range(5):
            idx_a = rng.choice(conflitantes) if conflitantes and rng.random() < 0.7 else rng.randrange(qtd_aulas)
            idx_b = rng.randrange(qtd_aulas)
            if idx_a == idx_b:
                continue
            slot_a, slot_b = cromossomo[idx_a], cromossomo[idx_b]
            if slot_a == slot_b:
                continue
            if (
                slot_b in contexto.slots_permitidos_set[idx_a]
                and slot_a in contexto.slots_permitidos_set[idx_b]
            ):
                return ("troca", idx_a, slot_a, idx_b, slot_b)

    idx_aula = rng.choice(conflitantes) if conflitantes and rng.random() < 0.7 else rng.randrange(qtd_aulas)
    permitidos = contexto.aulas[idx_aula].slots_permitidos
    if len(permitidos) <= 1:
        return None

    slot_antigo = cromossomo[idx_aula]
    slot_novo = rng.choice(permitidos)
    if slot_novo == slot_antigo:
        alternativas = [s for s in permitidos if s != slot_antigo]
        if not alternativas:
            return None
        slot_novo = rng.choice(alternativas)

    return ("mover", idx_aula, slot_antigo, slot_novo, 0)


def _aplicar_movimento(cromossomo: list[int], movimento: tuple[str, int, int, int, int]) -> None:
    """Aplica o movimento proposto diretamente no cromossomo."""
    tipo = movimento[0]
    if tipo == "mover":
        _, idx_aula, _, slot_novo, _ = movimento
        cromossomo[idx_aula] = slot_novo
    else:
        _, idx_a, slot_a, idx_b, slot_b = movimento
        cromossomo[idx_a] = slot_b
        cromossomo[idx_b] = slot_a


def _reverter_movimento(cromossomo: list[int], movimento: tuple[str, int, int, int, int]) -> None:
    """Desfaz o movimento caso ele não seja aceito pelo critério de Metropolis."""
    tipo = movimento[0]
    if tipo == "mover":
        _, idx_aula, slot_antigo, _, _ = movimento
        cromossomo[idx_aula] = slot_antigo
    else:
        _, idx_a, slot_a, idx_b, slot_b = movimento
        cromossomo[idx_a] = slot_a
        cromossomo[idx_b] = slot_b

"""Algoritmo Genético para exploração global do espaço de soluções de timetabling."""

import random
from dataclasses import dataclass
from typing import Callable, Sequence

from .avaliador import avaliar_solucao, identificar_aulas_em_conflito
from .dominio import ContextoExecucao, MetricasAvaliacao

AvaliadorFn = Callable[[Sequence[int], ContextoExecucao], MetricasAvaliacao]


@dataclass(frozen=True)
class ConfiguracaoAG:
    """Parâmetros de controle do Algoritmo Genético."""

    tamanho_populacao: int = 40
    geracoes: int = 60
    taxa_crossover: float = 0.85
    taxa_mutacao: float = 0.25
    tamanho_torneio: int = 3
    elitismo: int = 3
    fracao_inicializacao_gulosa: float = 0.7


def executar_algoritmo_genetico(
    contexto: ContextoExecucao,
    config: ConfiguracaoAG = ConfiguracaoAG(),
    rng: random.Random | None = None,
    avaliador: AvaliadorFn = avaliar_solucao,
) -> tuple[list[int], MetricasAvaliacao, list[float]]:
    """Evolui uma população de grades horárias e retorna o melhor indivíduo, métricas e histórico."""
    gerador = rng or random.Random()
    populacao = _inicializar_populacao(contexto, config, gerador)
    avaliacoes = [avaliador(ind, contexto) for ind in populacao]

    historico: list[float] = []
    melhor_idx = min(range(len(populacao)), key=lambda i: avaliacoes[i].custo_total)
    melhor_ind = list(populacao[melhor_idx])
    melhor_metrica = avaliacoes[melhor_idx]
    historico.append(melhor_metrica.custo_total)

    for _ in range(config.geracoes):
        indices_ordenados = sorted(range(len(populacao)), key=lambda i: avaliacoes[i].custo_total)
        nova_populacao = [list(populacao[i]) for i in indices_ordenados[: config.elitismo]]

        while len(nova_populacao) < config.tamanho_populacao:
            pai_a = _selecao_torneio(populacao, avaliacoes, config.tamanho_torneio, gerador)
            pai_b = _selecao_torneio(populacao, avaliacoes, config.tamanho_torneio, gerador)

            if gerador.random() < config.taxa_crossover:
                filho_a, filho_b = _crossover_uniforme(pai_a, pai_b, gerador)
            else:
                filho_a, filho_b = list(pai_a), list(pai_b)

            if gerador.random() < config.taxa_mutacao:
                _mutar_individuo(filho_a, contexto, gerador)
            if len(nova_populacao) + 1 < config.tamanho_populacao and gerador.random() < config.taxa_mutacao:
                _mutar_individuo(filho_b, contexto, gerador)

            nova_populacao.append(filho_a)
            if len(nova_populacao) < config.tamanho_populacao:
                nova_populacao.append(filho_b)

        populacao = nova_populacao
        avaliacoes = [avaliador(ind, contexto) for ind in populacao]

        idx_atual = min(range(len(populacao)), key=lambda i: avaliacoes[i].custo_total)
        if avaliacoes[idx_atual].custo_total < melhor_metrica.custo_total:
            melhor_ind = list(populacao[idx_atual])
            melhor_metrica = avaliacoes[idx_atual]

        historico.append(melhor_metrica.custo_total)

        if melhor_metrica.custo_total == 0:
            break

    return melhor_ind, melhor_metrica, historico


def _inicializar_populacao(
    contexto: ContextoExecucao,
    config: ConfiguracaoAG,
    rng: random.Random,
) -> list[list[int]]:
    """Gera a população inicial combinando heurística gulosa aleatorizada e geração aleatória."""
    qtd_gulosa = int(config.tamanho_populacao * config.fracao_inicializacao_gulosa)
    populacao: list[list[int]] = []

    for i in range(config.tamanho_populacao):
        if i < qtd_gulosa:
            populacao.append(_criar_individuo_guloso(contexto, rng))
        else:
            populacao.append(_criar_individuo_aleatorio(contexto, rng))

    return populacao


def _criar_individuo_aleatorio(contexto: ContextoExecucao, rng: random.Random) -> list[int]:
    """Cria um cromossomo escolhendo aleatoriamente um slot permitido para cada aula."""
    return [rng.choice(aula.slots_permitidos) for aula in contexto.aulas]


def _criar_individuo_guloso(contexto: ContextoExecucao, rng: random.Random) -> list[int]:
    """Cria um cromossomo evitando conflitos imediatos de professor e turma em ordem aleatória."""
    cromossomo = [0] * len(contexto.aulas)
    ordem_aulas = list(range(len(contexto.aulas)))
    rng.shuffle(ordem_aulas)

    ocupado_prof: set[tuple[str, int]] = set()
    ocupado_turma: set[tuple[str, int]] = set()

    for idx_aula in ordem_aulas:
        aula = contexto.aulas[idx_aula]
        livres = [
            s
            for s in aula.slots_permitidos
            if (aula.professor_id, s) not in ocupado_prof and (aula.turma_id, s) not in ocupado_turma
        ]
        slot_escolhido = rng.choice(livres) if livres else rng.choice(aula.slots_permitidos)
        cromossomo[idx_aula] = slot_escolhido
        ocupado_prof.add((aula.professor_id, slot_escolhido))
        ocupado_turma.add((aula.turma_id, slot_escolhido))

    return cromossomo


def _selecao_torneio(
    populacao: Sequence[list[int]],
    avaliacoes: Sequence[MetricasAvaliacao],
    tamanho_torneio: int,
    rng: random.Random,
) -> list[int]:
    """Seleciona o melhor indivíduo entre k candidatos sorteados aleatoriamente."""
    candidatos = rng.sample(range(len(populacao)), k=min(tamanho_torneio, len(populacao)))
    vencedor = min(candidatos, key=lambda i: avaliacoes[i].custo_total)
    return populacao[vencedor]


def _crossover_uniforme(
    pai_a: Sequence[int],
    pai_b: Sequence[int],
    rng: random.Random,
) -> tuple[list[int], list[int]]:
    """Combina dois pais gene a gene com probabilidade uniforme."""
    filho_a: list[int] = []
    filho_b: list[int] = []
    for gene_a, gene_b in zip(pai_a, pai_b):
        if rng.random() < 0.5:
            filho_a.append(gene_a)
            filho_b.append(gene_b)
        else:
            filho_a.append(gene_b)
            filho_b.append(gene_a)
    return filho_a, filho_b


def _mutar_individuo(
    cromossomo: list[int],
    contexto: ContextoExecucao,
    rng: random.Random,
) -> None:
    """Aplica mutação direcionada a conflitos quando existentes ou em uma aula aleatória."""
    conflitantes = identificar_aulas_em_conflito(cromossomo, contexto)
    if conflitantes and rng.random() < 0.8:
        idx_aula = rng.choice(conflitantes)
    else:
        idx_aula = rng.randrange(len(cromossomo))

    permitidos = contexto.aulas[idx_aula].slots_permitidos
    if len(permitidos) > 1:
        atual = cromossomo[idx_aula]
        alternativas = [s for s in permitidos if s != atual]
        if alternativas:
            cromossomo[idx_aula] = rng.choice(alternativas)

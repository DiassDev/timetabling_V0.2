"""Modelos de domínio, resultados e exceções do motor de timetabling."""

from dataclasses import dataclass, field
from enum import Enum


class DiaSemana(str, Enum):
    SEGUNDA = "segunda"
    TERCA = "terca"
    QUARTA = "quarta"
    QUINTA = "quinta"
    SEXTA = "sexta"
    SABADO = "sabado"


class Turno(str, Enum):
    MANHA = "manha"
    TARDE = "tarde"
    NOITE = "noite"


class InviabilidadeErro(Exception):
    """Erro de domínio lançado quando a instância não possui solução possível."""


@dataclass(frozen=True)
class Slot:
    """Representa um horário disponível no universo de geração."""

    id: str
    dia: DiaSemana
    turno: Turno
    inicio_minutos: int
    duracao_minutos: int

    @property
    def fim_minutos(self) -> int:
        return self.inicio_minutos + self.duracao_minutos


@dataclass(frozen=True)
class Professor:
    """Representa um docente e o conjunto de slots em que está disponível."""

    id: str
    nome: str
    disponibilidade: frozenset[str]


@dataclass(frozen=True)
class Disciplina:
    """Representa uma disciplina cadastrada no sistema."""

    id: str
    nome: str


@dataclass(frozen=True)
class Turma:
    """Representa uma turma vinculada a um curso e turno."""

    id: str
    nome: str
    curso: str
    turno: Turno


@dataclass(frozen=True)
class Alocacao:
    """Entrada manual do coordenador definindo professor, disciplina, turma e carga semanal."""

    id: str
    professor_id: str
    disciplina_id: str
    turma_id: str
    carga_horaria: int


@dataclass(frozen=True)
class Aula:
    """Unidade indivisível de uma alocação a ser posicionada em exatamente um slot."""

    indice: int
    alocacao_id: str
    professor_id: str
    disciplina_id: str
    turma_id: str
    slots_permitidos: tuple[int, ...]


@dataclass(frozen=True)
class InstanciaTimetabling:
    """Agrupa todos os dados de entrada necessários para a geração da grade."""

    slots: tuple[Slot, ...]
    professores: tuple[Professor, ...]
    disciplinas: tuple[Disciplina, ...]
    turmas: tuple[Turma, ...]
    alocacoes: tuple[Alocacao, ...]


@dataclass(frozen=True)
class ContextoExecucao:
    """Estrutura indexada derivada da instância para acesso rápido pelas heurísticas."""

    instancia: InstanciaTimetabling
    aulas: tuple[Aula, ...]
    slots: tuple[Slot, ...]
    ordem_slot_no_bloco: dict[int, tuple[tuple[DiaSemana, Turno], int]]
    indice_professor: dict[str, int]
    indice_turma: dict[str, int]
    slots_permitidos_set: tuple[frozenset[int], ...]


@dataclass(frozen=True)
class MetricasAvaliacao:
    """Detalhamento das violações fortes, fracas e custo total de uma solução."""

    conflitos_professor: int
    conflitos_turma: int
    fora_disponibilidade: int
    janelas_professor: int
    janelas_turma: int
    custo_total: float

    @property
    def violacoes_fortes(self) -> int:
        return self.conflitos_professor + self.conflitos_turma + self.fora_disponibilidade

    @property
    def violacoes_fracas(self) -> int:
        return self.janelas_professor + self.janelas_turma

    @property
    def valida(self) -> bool:
        return self.violacoes_fortes == 0


@dataclass(frozen=True)
class ItemGrade:
    """Representa uma aula já alocada em um slot específico na grade final."""

    alocacao_id: str
    professor_id: str
    disciplina_id: str
    turma_id: str
    slot: Slot


@dataclass(frozen=True)
class ResultadoOtimizacao:
    """Resultado completo retornado pelo motor híbrido após a execução."""

    grade: tuple[ItemGrade, ...]
    metricas: MetricasAvaliacao
    tempo_execucao_segundos: float
    historico_custo_ga: list[float] = field(default_factory=list)
    historico_custo_sa: list[float] = field(default_factory=list)

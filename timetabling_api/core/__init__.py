"""Motor matemático de timetabling baseado em Algoritmo Genético e Simulated Annealing."""

from .avaliador import PesosAvaliacao, avaliar_solucao
from .dominio import (
    Alocacao,
    DiaSemana,
    Disciplina,
    InstanciaTimetabling,
    InviabilidadeErro,
    ItemGrade,
    MetricasAvaliacao,
    Professor,
    ResultadoOtimizacao,
    Slot,
    Turma,
    Turno,
)
from .genetico import ConfiguracaoAG
from .motor import ConfiguracaoMotor, gerar_horario
from .simulated_annealing import ConfiguracaoSA
from .validador import validar_instancia

__all__ = [
    "Alocacao",
    "ConfiguracaoAG",
    "ConfiguracaoMotor",
    "ConfiguracaoSA",
    "DiaSemana",
    "Disciplina",
    "InstanciaTimetabling",
    "InviabilidadeErro",
    "ItemGrade",
    "MetricasAvaliacao",
    "PesosAvaliacao",
    "Professor",
    "ResultadoOtimizacao",
    "Slot",
    "Turma",
    "Turno",
    "avaliar_solucao",
    "gerar_horario",
    "validar_instancia",
]

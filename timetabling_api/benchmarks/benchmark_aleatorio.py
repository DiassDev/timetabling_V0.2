"""Bateria de testes aleatórios para avaliar robustez e performance do motor híbrido."""

import random
import statistics
import time

from timetabling_api.benchmarks.dados_teste import criar_slots_padrao
from timetabling_api.core import (
    Alocacao,
    ConfiguracaoAG,
    ConfiguracaoMotor,
    ConfiguracaoSA,
    Disciplina,
    InstanciaTimetabling,
    InviabilidadeErro,
    Professor,
    Turma,
    Turno,
    gerar_horario,
)


def gerar_instancia_aleatoria(
    qtd_professores: int,
    qtd_turmas_manha: int,
    qtd_turmas_noite: int,
    folga_disponibilidade: int,
    semente: int,
) -> InstanciaTimetabling:
    """Gera uma instância aleatória variando porte, cargas e folga de disponibilidade."""
    rng = random.Random(semente)
    slots = criar_slots_padrao(aulas_por_turno=4)
    slots_manha = [s.id for s in slots if s.turno == Turno.MANHA]
    slots_noite = [s.id for s in slots if s.turno == Turno.NOITE]

    disciplinas = tuple(Disciplina(f"D{i}", f"Disciplina {i}") for i in range(1, 15))
    turmas = tuple(
        [Turma(f"TM{i}", f"Manha {i}", "Médio", Turno.MANHA) for i in range(1, qtd_turmas_manha + 1)]
        + [Turma(f"TN{i}", f"Noite {i}", "Superior", Turno.NOITE) for i in range(1, qtd_turmas_noite + 1)]
    )

    # Garante uma grade base factível por turno antes de sortear disponibilidades extras
    alocacoes: list[Alocacao] = []
    slots_usados_prof_manha: dict[int, set[str]] = {i: set() for i in range(1, qtd_professores + 1)}
    slots_usados_prof_noite: dict[int, set[str]] = {i: set() for i in range(1, qtd_professores + 1)}
    idx_aloc = 1

    for turma in turmas:
        pool_slots = list(slots_manha if turma.turno == Turno.MANHA else slots_noite)
        rng.shuffle(pool_slots)
        usados_prof = slots_usados_prof_manha if turma.turno == Turno.MANHA else slots_usados_prof_noite

        total_aulas_turma = rng.randint(15, 19)
        cargas = _particionar_carga(total_aulas_turma, rng)
        pos_slot = 0

        for carga in cargas:
            slots_da_aloc = pool_slots[pos_slot : pos_slot + carga]
            pos_slot += carga
            candidatos = [
                p
                for p in range(1, qtd_professores + 1)
                if all(s not in usados_prof[p] for s in slots_da_aloc)
            ]
            prof_num = rng.choice(candidatos)
            usados_prof[prof_num].update(slots_da_aloc)

            disc = rng.choice(disciplinas)
            alocacoes.append(
                Alocacao(
                    id=f"A{idx_aloc}",
                    professor_id=f"P{prof_num}",
                    disciplina_id=disc.id,
                    turma_id=turma.id,
                    carga_horaria=carga,
                )
            )
            idx_aloc += 1

    professores: list[Professor] = []
    for p in range(1, qtd_professores + 1):
        disp = set(slots_usados_prof_manha[p]) | set(slots_usados_prof_noite[p])
        extras_m = [s for s in slots_manha if s not in disp]
        extras_n = [s for s in slots_noite if s not in disp]

        if slots_usados_prof_manha[p]:
            disp.update(rng.sample(extras_m, min(len(extras_m), folga_disponibilidade)))
        if slots_usados_prof_noite[p]:
            disp.update(rng.sample(extras_n, min(len(extras_n), folga_disponibilidade)))
        if not disp:
            disp.update(rng.sample(slots_manha, min(len(slots_manha), 6)))

        professores.append(Professor(f"P{p}", f"Prof {p:02d}", frozenset(disp)))

    return InstanciaTimetabling(
        slots=slots,
        professores=tuple(professores),
        disciplinas=disciplinas,
        turmas=turmas,
        alocacoes=tuple(alocacoes),
    )


def _particionar_carga(total: int, rng: random.Random) -> list[int]:
    """Divide a carga semanal da turma em disciplinas de 2 a 4 aulas."""
    cargas: list[int] = []
    restante = total
    while restante > 0:
        if restante <= 4:
            cargas.append(restante)
            break
        parte = rng.choice([2, 3, 4])
        if restante - parte == 1:
            parte = 2
        cargas.append(parte)
        restante -= parte
    return cargas


def executar_cenario(
    nome: str,
    qtd_execucoes: int,
    qtd_professores: int,
    qtd_turmas_manha: int,
    qtd_turmas_noite: int,
    folga_disponibilidade: int,
    config: ConfiguracaoMotor,
) -> None:
    """Executa múltiplas instâncias aleatórias para um cenário e imprime estatísticas."""
    validas = 0
    tempos: list[float] = []
    fortes: list[int] = []
    fracas: list[int] = []
    aulas_totais: list[int] = []

    for i in range(qtd_execucoes):
        instancia = gerar_instancia_aleatoria(
            qtd_professores=qtd_professores,
            qtd_turmas_manha=qtd_turmas_manha,
            qtd_turmas_noite=qtd_turmas_noite,
            folga_disponibilidade=folga_disponibilidade,
            semente=1000 + i * 17,
        )
        try:
            res = gerar_horario(
                instancia,
                ConfiguracaoMotor(ag=config.ag, sa=config.sa, semente=2000 + i),
            )
            m = res.metricas
            if m.valida:
                validas += 1
            tempos.append(res.tempo_execucao_segundos)
            fortes.append(m.violacoes_fortes)
            fracas.append(m.violacoes_fracas)
            aulas_totais.append(len(res.grade))
        except InviabilidadeErro as erro:
            print(f"  [Inviável #{i}] {erro}")

    print(f"=== {nome} ({qtd_execucoes} execuções) ===")
    print(f"Aulas/instância : {min(aulas_totais)}..{max(aulas_totais)}")
    print(f"Soluções válidas: {validas}/{qtd_execucoes} ({100 * validas / qtd_execucoes:.1f}%)")
    print(f"Violações fortes: mín={min(fortes)}, máx={max(fortes)}, média={statistics.mean(fortes):.2f}")
    print(f"Violações fracas: mín={min(fracas)}, máx={max(fracas)}, média={statistics.mean(fracas):.2f}")
    print(
        f"Tempo (s)       : mín={min(tempos):.3f}s, máx={max(tempos):.3f}s, "
        f"média={statistics.mean(tempos):.3f}s\n"
    )


def main() -> None:
    inicio_geral = time.perf_counter()
    config_padrao = ConfiguracaoMotor(
        ag=ConfiguracaoAG(tamanho_populacao=40, geracoes=50),
        sa=ConfiguracaoSA(temperatura_inicial=350.0, taxa_resfriamento=0.985, iteracoes_por_temperatura=15),
    )

    executar_cenario("Porte Médio (25 profs, 8 turmas, folga=4)", 5, 25, 4, 4, 4, config_padrao)
    executar_cenario("Referência Folgada (50 profs, 14 turmas, folga=5)", 5, 50, 7, 7, 5, config_padrao)
    executar_cenario("Referência Apertada (50 profs, 14 turmas, folga=2)", 5, 50, 7, 7, 2, config_padrao)
    executar_cenario("Escala Alta (60 profs, 18 turmas, folga=4)", 3, 60, 9, 9, 4, config_padrao)

    print(f"Tempo total da bateria: {time.perf_counter() - inicio_geral:.2f}s")


if __name__ == "__main__":
    main()

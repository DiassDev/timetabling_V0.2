"""Script de demonstração e verificação do motor híbrido (AG + SA) com dados simulados."""

from timetabling_api.benchmarks.dados_teste import gerar_instancia_pequena, gerar_instancia_referencia
from timetabling_api.core import ConfiguracaoAG, ConfiguracaoMotor, ConfiguracaoSA, gerar_horario


def exibir_resumo(titulo: str, resultado) -> None:
    """Exibe métricas principais do resultado de otimização."""
    m = resultado.metricas
    print(f"=== {titulo} ===")
    print(f"Total de aulas alocadas : {len(resultado.grade)}")
    print(f"Solução válida          : {'Sim' if m.valida else 'Não'}")
    print(f"Violações fortes        : {m.violacoes_fortes} "
          f"(prof={m.conflitos_professor}, turma={m.conflitos_turma}, disp={m.fora_disponibilidade})")
    print(f"Violações fracas        : {m.violacoes_fracas} "
          f"(janelas_prof={m.janelas_professor}, janelas_turma={m.janelas_turma})")
    print(f"Custo final             : {m.custo_total:.2f}")
    print(f"Evolução AG (início->fim): {resultado.historico_custo_ga[0]:.1f} -> {resultado.historico_custo_ga[-1]:.1f}")
    print(f"Evolução SA (início->fim): {resultado.historico_custo_sa[0]:.1f} -> {resultado.historico_custo_sa[-1]:.1f}")
    print(f"Tempo de execução       : {resultado.tempo_execucao_segundos:.3f}s\n")


def main() -> None:
    instancia_pequena = gerar_instancia_pequena()
    res_pequena = gerar_horario(instancia_pequena, ConfiguracaoMotor(semente=42))
    exibir_resumo("Instância Pequena", res_pequena)

    instancia_ref = gerar_instancia_referencia(semente=42)
    config_ref = ConfiguracaoMotor(
        ag=ConfiguracaoAG(tamanho_populacao=40, geracoes=50),
        sa=ConfiguracaoSA(temperatura_inicial=350.0, taxa_resfriamento=0.985, iteracoes_por_temperatura=15),
        semente=42,
    )
    res_ref = gerar_horario(instancia_ref, config_ref)
    exibir_resumo("Instância de Referência (50 profs, 14 turmas, manhã/noite)", res_ref)


if __name__ == "__main__":
    main()

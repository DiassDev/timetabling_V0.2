"""Modelos relacionais Django espelhando exatamente a modelagem de docs/queries.sql em SQLite3."""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class PapelUsuario(models.TextChoices):
    ADMIN = "ADMIN", "Administrador"
    COORDENADOR = "COORDENADOR", "Coordenador"
    PROFESSOR = "PROFESSOR", "Professor"


class NivelEnsino(models.TextChoices):
    FUNDAMENTAL = "FUNDAMENTAL", "Ensino Fundamental"
    MEDIO = "MEDIO", "Ensino Médio"


class Turno(models.TextChoices):
    MANHA = "MANHA", "Manhã"
    TARDE = "TARDE", "Tarde"
    NOITE = "NOITE", "Noite"


class DiaSemana(models.TextChoices):
    SEG = "SEG", "Segunda-feira"
    TER = "TER", "Terça-feira"
    QUA = "QUA", "Quarta-feira"
    QUI = "QUI", "Quinta-feira"
    SEX = "SEX", "Sexta-feira"
    SAB = "SAB", "Sábado"


class StatusExecucao(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    EM_EXECUCAO = "EM_EXECUCAO", "Em execução"
    CONCLUIDA = "CONCLUIDA", "Concluída"
    FALHA = "FALHA", "Falha"


class TipoDiagnostico(models.TextChoices):
    DISPONIBILIDADE = "DISPONIBILIDADE", "Disponibilidade"
    CONFLITO = "CONFLITO", "Conflito"
    CAPACIDADE = "CAPACIDADE", "Capacidade"
    OUTRO = "OUTRO", "Outro"


class Usuario(models.Model):
    """Usuário do sistema com papel único e regra de administrador único no banco."""

    email = models.EmailField(max_length=150, unique=True)
    senha_hash = models.CharField(max_length=255)
    papel = models.CharField(max_length=20, choices=PapelUsuario.choices)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuario"
        constraints = [
            models.CheckConstraint(
                condition=Q(papel__in=PapelUsuario.values),
                name="ck_usuario_papel",
            ),
            models.UniqueConstraint(
                fields=["papel"],
                condition=Q(papel=PapelUsuario.ADMIN),
                name="uq_admin_unico",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.papel})"


class Disciplina(models.Model):
    """Disciplina acadêmica reutilizável entre cursos e turmas."""

    nome = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "disciplina"

    def __str__(self) -> str:
        return self.nome


class Professor(models.Model):
    """Docente vinculado a um usuário e habilitado para lecionar disciplinas."""

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.PROTECT,
        db_column="usuario_id",
        related_name="professor",
    )
    matricula = models.CharField(max_length=20, unique=True)
    disciplinas = models.ManyToManyField(
        Disciplina,
        through="ProfessorDisciplina",
        related_name="professores",
    )

    class Meta:
        db_table = "professor"

    def __str__(self) -> str:
        return f"{self.matricula} - {self.usuario.email}"


class PeriodoLetivo(models.Model):
    """Período letivo que delimita turmas, disponibilidades e gerações."""

    rotulo = models.CharField(max_length=50, unique=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "periodo_letivo"
        constraints = [
            models.CheckConstraint(
                condition=Q(data_fim__gte=F("data_inicio")),
                name="ck_periodo_letivo_datas",
            ),
        ]

    def __str__(self) -> str:
        return self.rotulo


class Curso(models.Model):
    """Curso oferecido pela instituição."""

    nome = models.CharField(max_length=120, unique=True)
    nivel_ensino = models.CharField(max_length=20, choices=NivelEnsino.choices)

    class Meta:
        db_table = "curso"
        constraints = [
            models.CheckConstraint(
                condition=Q(nivel_ensino__in=NivelEnsino.values),
                name="ck_curso_nivel_ensino",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.nivel_ensino})"


class CursoDisciplina(models.Model):
    """Carga horária semanal de uma disciplina em determinada série do curso."""

    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, db_column="curso_id")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, db_column="disciplina_id")
    serie = models.CharField(max_length=20)
    aulas_semana = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "curso_disciplina"
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "disciplina", "serie"],
                name="uq_curso_disciplina_curso_disc_serie",
            ),
            models.CheckConstraint(
                condition=Q(aulas_semana__gt=0),
                name="ck_curso_disciplina_aulas_positivas",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.curso.nome} - {self.serie} - {self.disciplina.nome}"


class Turma(models.Model):
    """Turma vinculada a um curso, período letivo e turno."""

    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, db_column="curso_id")
    periodo_letivo = models.ForeignKey(
        PeriodoLetivo,
        on_delete=models.PROTECT,
        db_column="periodo_letivo_id",
    )
    serie = models.CharField(max_length=20)
    identificador = models.CharField(max_length=20)
    turno = models.CharField(max_length=20, choices=Turno.choices)
    qtd_alunos = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "turma"
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "periodo_letivo", "serie", "identificador"],
                name="uq_turma_curso_periodo_serie_id",
            ),
            models.CheckConstraint(
                condition=Q(turno__in=Turno.values),
                name="ck_turma_turno",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.serie} {self.identificador} ({self.turno})"


class PeriodoAula(models.Model):
    """Definição de faixa horária dentro de um turno sem sobreposição."""

    turno = models.CharField(max_length=20, choices=Turno.choices)
    ordem = models.PositiveSmallIntegerField()
    hora_inicio = models.TimeField()
    duracao_min = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "periodo_aula"
        constraints = [
            models.UniqueConstraint(
                fields=["turno", "ordem"],
                name="uq_periodo_aula_turno_ordem",
            ),
            models.CheckConstraint(
                condition=Q(turno__in=Turno.values),
                name="ck_periodo_aula_turno",
            ),
            models.CheckConstraint(
                condition=Q(duracao_min__gt=0),
                name="ck_periodo_aula_duracao_positiva",
            ),
        ]

    def clean(self) -> None:
        """Impede cadastro de períodos de aula sobrepostos no mesmo turno."""
        super().clean()
        if not self.hora_inicio or not self.duracao_min:
            return
        base = datetime(2000, 1, 1)
        inicio_novo = datetime.combine(base.date(), self.hora_inicio)
        fim_novo = inicio_novo + timedelta(minutes=self.duracao_min)

        existentes = PeriodoAula.objects.filter(turno=self.turno).exclude(pk=self.pk)
        for outro in existentes:
            inicio_outro = datetime.combine(base.date(), outro.hora_inicio)
            fim_outro = inicio_outro + timedelta(minutes=outro.duracao_min)
            if inicio_novo < fim_outro and inicio_outro < fim_novo:
                raise ValidationError(
                    f"Sobreposição de horário detectada no turno {self.turno} com a ordem {outro.ordem}."
                )

    def __str__(self) -> str:
        return f"{self.turno} #{self.ordem} ({self.hora_inicio})"


class Slot(models.Model):
    """Combinação única de período de aula e dia da semana."""

    periodo_aula = models.ForeignKey(
        PeriodoAula,
        on_delete=models.PROTECT,
        db_column="periodo_aula_id",
        related_name="slots",
    )
    dia_semana = models.CharField(max_length=20, choices=DiaSemana.choices)

    class Meta:
        db_table = "slot"
        constraints = [
            models.UniqueConstraint(
                fields=["periodo_aula", "dia_semana"],
                name="uq_slot_periodo_dia",
            ),
            models.CheckConstraint(
                condition=Q(dia_semana__in=DiaSemana.values),
                name="ck_slot_dia",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.dia_semana} - {self.periodo_aula}"


class ProfessorDisciplina(models.Model):
    """Relação N:N entre professores e disciplinas que estão aptos a lecionar."""

    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, db_column="professor_id")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, db_column="disciplina_id")

    class Meta:
        db_table = "professor_disciplina"
        constraints = [
            models.UniqueConstraint(
                fields=["professor", "disciplina"],
                name="uq_professor_disciplina",
            ),
        ]


class Disponibilidade(models.Model):
    """Declaração de disponibilidade do professor em um slot e período letivo."""

    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, db_column="professor_id")
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, db_column="slot_id")
    periodo_letivo = models.ForeignKey(
        PeriodoLetivo,
        on_delete=models.PROTECT,
        db_column="periodo_letivo_id",
    )

    class Meta:
        db_table = "disponibilidade"
        constraints = [
            models.UniqueConstraint(
                fields=["professor", "slot", "periodo_letivo"],
                name="uq_disponibilidade_prof_slot_periodo",
            ),
        ]


class Alocacao(models.Model):
    """Atribuição manual de professor, disciplina, turma e carga semanal."""

    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, db_column="turma_id")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, db_column="disciplina_id")
    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, db_column="professor_id")
    aulas_semana = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "alocacao"
        constraints = [
            models.UniqueConstraint(
                fields=["turma", "disciplina"],
                name="uq_alocacao_turma_disciplina",
            ),
            models.UniqueConstraint(
                fields=["id", "professor", "turma"],
                name="uq_alocacao_prof_turma",
            ),
            models.CheckConstraint(
                condition=Q(aulas_semana__gt=0),
                name="ck_alocacao_aulas_positivas",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.turma} | {self.disciplina} | {self.professor} ({self.aulas_semana}h)"


class PreferenciaDisciplina(models.Model):
    """Ordenação opcional de preferência de disciplinas por professor."""

    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, db_column="professor_id")
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, db_column="disciplina_id")
    ordem = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "preferencia_disciplina"
        constraints = [
            models.UniqueConstraint(
                fields=["professor", "ordem"],
                name="uq_preferencia_professor_ordem",
            ),
        ]


class ExecucaoGeracao(models.Model):
    """Registro histórico de uma execução do motor de geração de horários."""

    periodo_letivo = models.ForeignKey(
        PeriodoLetivo,
        on_delete=models.PROTECT,
        db_column="periodo_letivo_id",
    )
    solicitado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="solicitado_por",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusExecucao.choices,
        default=StatusExecucao.PENDENTE,
    )
    iniciada_em = models.DateTimeField(null=True, blank=True)
    concluida_em = models.DateTimeField(null=True, blank=True)
    algoritmo = models.CharField(max_length=50, null=True, blank=True)
    parametros = models.JSONField(null=True, blank=True)
    violacoes_fracas = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "execucao_geracao"
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=StatusExecucao.values),
                name="ck_execucao_status",
            ),
        ]


class AulaAgendada(models.Model):
    """Resultado de alocação de uma aula em um slot dentro de uma execução."""

    execucao = models.ForeignKey(
        ExecucaoGeracao,
        on_delete=models.PROTECT,
        db_column="execucao_id",
        related_name="aulas_agendadas",
    )
    alocacao = models.ForeignKey(Alocacao, on_delete=models.PROTECT, db_column="alocacao_id")
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, db_column="slot_id")
    professor = models.ForeignKey(Professor, on_delete=models.PROTECT, db_column="professor_id")
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, db_column="turma_id")

    class Meta:
        db_table = "aula_agendada"
        constraints = [
            models.UniqueConstraint(
                fields=["execucao", "professor", "slot"],
                name="uq_aula_execucao_professor_slot",
            ),
            models.UniqueConstraint(
                fields=["execucao", "turma", "slot"],
                name="uq_aula_execucao_turma_slot",
            ),
        ]

    def clean(self) -> None:
        """Garante consistência entre professor/turma informados e a alocação referenciada."""
        super().clean()
        if self.alocacao_id:
            if self.professor_id != self.alocacao.professor_id or self.turma_id != self.alocacao.turma_id:
                raise ValidationError(
                    "Professor e turma da aula agendada devem corresponder exatamente à alocação."
                )


class DiagnosticoInviabilidade(models.Model):
    """Registro de causa de inviabilidade em linguagem de domínio."""

    execucao = models.ForeignKey(
        ExecucaoGeracao,
        on_delete=models.PROTECT,
        db_column="execucao_id",
        related_name="diagnosticos",
    )
    tipo = models.CharField(max_length=20, choices=TipoDiagnostico.choices)
    mensagem = models.TextField()

    class Meta:
        db_table = "diagnostico_inviabilidade"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=TipoDiagnostico.values),
                name="ck_diagnostico_tipo",
            ),
        ]

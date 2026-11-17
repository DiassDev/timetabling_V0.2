"""Serializers do Django REST Framework para comunicação com o frontend."""

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import (
    Alocacao,
    AulaAgendada,
    Curso,
    CursoDisciplina,
    DiagnosticoInviabilidade,
    Disciplina,
    Disponibilidade,
    ExecucaoGeracao,
    PeriodoAula,
    PeriodoLetivo,
    PreferenciaDisciplina,
    Professor,
    ProfessorDisciplina,
    Slot,
    Turma,
    Usuario,
)


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializa usuários mantendo a senha protegida (write-only)."""

    senha = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ["id", "email", "papel", "ativo", "senha"]

    def create(self, validated_data: dict) -> Usuario:
        senha = validated_data.pop("senha", "")
        validated_data["senha_hash"] = make_password(senha)
        return super().create(validated_data)

    def update(self, instance: Usuario, validated_data: dict) -> Usuario:
        senha = validated_data.pop("senha", None)
        if senha is not None:
            validated_data["senha_hash"] = make_password(senha)
        return super().update(instance, validated_data)


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = "__all__"


class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = ["id", "usuario", "matricula", "disciplinas"]


class ProfessorDisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessorDisciplina
        fields = "__all__"


class PeriodoLetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoLetivo
        fields = "__all__"


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"


class CursoDisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CursoDisciplina
        fields = "__all__"


class TurmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turma
        fields = "__all__"


class PeriodoAulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAula
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:
        instancia = PeriodoAula(**attrs)
        if self.instance is not None:
            instancia.pk = self.instance.pk
        instancia.clean()
        return attrs


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = "__all__"


class DisponibilidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilidade
        fields = "__all__"


class AlocacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alocacao
        fields = "__all__"


class PreferenciaDisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferenciaDisciplina
        fields = "__all__"


class DiagnosticoInviabilidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticoInviabilidade
        fields = "__all__"


class AulaAgendadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AulaAgendada
        fields = "__all__"


class ExecucaoGeracaoSerializer(serializers.ModelSerializer):
    aulas_agendadas = AulaAgendadaSerializer(many=True, read_only=True)
    diagnosticos = DiagnosticoInviabilidadeSerializer(many=True, read_only=True)

    class Meta:
        model = ExecucaoGeracao
        fields = [
            "id",
            "periodo_letivo",
            "solicitado_por",
            "status",
            "iniciada_em",
            "concluida_em",
            "algoritmo",
            "parametros",
            "violacoes_fracas",
            "aulas_agendadas",
            "diagnosticos",
        ]


class SolicitarGeracaoSerializer(serializers.Serializer):
    """Payload de entrada para acionar a geração automática de horários."""

    periodo_letivo_id = serializers.IntegerField()
    solicitado_por_id = serializers.IntegerField()
    semente = serializers.IntegerField(required=False, allow_null=True, default=None)

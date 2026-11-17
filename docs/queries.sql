-- =====================================================================
-- SISTEMA DE TIMETABLING ESCOLAR
-- MySQL 8 - Versão compatível com OneCompiler
--
-- IMPORTANTE:
-- 1. NÃO utilizar CREATE DATABASE.
-- 2. NÃO utilizar USE.
-- 3. Os TRIGGERS foram retirados deste script principal porque
--    o OneCompiler pode interpretar os ";" internos de BEGIN/END
--    como final de comandos.
-- 4. Os testes de integridade que propositalmente geram erros
--    ficam no final, comentados.
-- =====================================================================


-- =====================================================================
-- 1. TABELA USUARIO
-- =====================================================================

CREATE TABLE usuario (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(150) NOT NULL,
    senha_hash  VARCHAR(255) NOT NULL,
    papel       VARCHAR(20) NOT NULL,
    ativo       TINYINT(1) NOT NULL DEFAULT 1,

    CONSTRAINT uq_usuario_email
        UNIQUE (email)
) ENGINE=InnoDB;


-- =====================================================================
-- 2. TABELA PROFESSOR
-- =====================================================================

CREATE TABLE professor (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  BIGINT NOT NULL,
    matricula   VARCHAR(20) NOT NULL,

    CONSTRAINT uq_professor_usuario_id
        UNIQUE (usuario_id),

    CONSTRAINT uq_professor_matricula
        UNIQUE (matricula),

    CONSTRAINT fk_professor_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 3. TABELA PERIODO_LETIVO
-- =====================================================================

CREATE TABLE periodo_letivo (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    rotulo       VARCHAR(50) NOT NULL,
    data_inicio  DATE NOT NULL,
    data_fim     DATE NOT NULL,
    ativo        TINYINT(1) NOT NULL DEFAULT 1,

    CONSTRAINT uq_periodo_letivo_rotulo
        UNIQUE (rotulo)
) ENGINE=InnoDB;


-- =====================================================================
-- 4. TABELA CURSO
-- =====================================================================

CREATE TABLE curso (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    nivel_ensino  VARCHAR(20) NOT NULL,

    CONSTRAINT uq_curso_nome
        UNIQUE (nome),

    CONSTRAINT ck_curso_nivel_ensino
        CHECK (nivel_ensino IN ('FUNDAMENTAL', 'MEDIO'))
) ENGINE=InnoDB;


-- =====================================================================
-- 5. TABELA DISCIPLINA
-- =====================================================================

CREATE TABLE disciplina (
    id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome  VARCHAR(120) NOT NULL,

    CONSTRAINT uq_disciplina_nome
        UNIQUE (nome)
) ENGINE=InnoDB;


-- =====================================================================
-- 6. TABELA CURSO_DISCIPLINA
-- =====================================================================

CREATE TABLE curso_disciplina (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    curso_id       BIGINT NOT NULL,
    disciplina_id  BIGINT NOT NULL,
    serie          VARCHAR(20) NOT NULL,
    aulas_semana   SMALLINT NOT NULL,

    CONSTRAINT uq_curso_disciplina_curso_disc_serie
        UNIQUE (curso_id, disciplina_id, serie),

    CONSTRAINT fk_curso_disciplina_curso
        FOREIGN KEY (curso_id)
        REFERENCES curso (id),

    CONSTRAINT fk_curso_disciplina_disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES disciplina (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 7. TABELA TURMA
-- =====================================================================

CREATE TABLE turma (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    curso_id           BIGINT NOT NULL,
    periodo_letivo_id  BIGINT NOT NULL,
    serie              VARCHAR(20) NOT NULL,
    identificador      VARCHAR(20) NOT NULL,
    turno              VARCHAR(20) NOT NULL,
    qtd_alunos         SMALLINT NOT NULL,

    CONSTRAINT uq_turma_curso_periodo_serie_id
        UNIQUE (
            curso_id,
            periodo_letivo_id,
            serie,
            identificador
        ),

    CONSTRAINT ck_turma_turno
        CHECK (turno IN ('MANHA', 'TARDE', 'NOITE')),

    CONSTRAINT fk_turma_curso
        FOREIGN KEY (curso_id)
        REFERENCES curso (id),

    CONSTRAINT fk_turma_periodo_letivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES periodo_letivo (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 8. TABELA PERIODO_AULA
-- =====================================================================

CREATE TABLE periodo_aula (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    turno        VARCHAR(20) NOT NULL,
    ordem        SMALLINT NOT NULL,
    hora_inicio  TIME NOT NULL,
    duracao_min  SMALLINT NOT NULL,

    CONSTRAINT uq_periodo_aula_turno_ordem
        UNIQUE (turno, ordem),

    CONSTRAINT ck_periodo_aula_turno
        CHECK (turno IN ('MANHA', 'TARDE', 'NOITE'))
) ENGINE=InnoDB;


-- =====================================================================
-- 9. TABELA SLOT
-- =====================================================================

CREATE TABLE slot (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    periodo_aula_id  BIGINT NOT NULL,
    dia_semana       VARCHAR(20) NOT NULL,

    CONSTRAINT uq_slot_periodo_dia
        UNIQUE (periodo_aula_id, dia_semana),

    CONSTRAINT ck_slot_dia
        CHECK (
            dia_semana IN (
                'SEG',
                'TER',
                'QUA',
                'QUI',
                'SEX',
                'SAB'
            )
        ),

    CONSTRAINT fk_slot_periodo_aula
        FOREIGN KEY (periodo_aula_id)
        REFERENCES periodo_aula (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 10. TABELA PROFESSOR_DISCIPLINA
-- =====================================================================

CREATE TABLE professor_disciplina (
    professor_id   BIGINT NOT NULL,
    disciplina_id  BIGINT NOT NULL,

    PRIMARY KEY (
        professor_id,
        disciplina_id
    ),

    CONSTRAINT fk_prof_disc_professor
        FOREIGN KEY (professor_id)
        REFERENCES professor (id),

    CONSTRAINT fk_prof_disc_disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES disciplina (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 11. TABELA DISPONIBILIDADE
-- =====================================================================

CREATE TABLE disponibilidade (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    professor_id       BIGINT NOT NULL,
    slot_id            BIGINT NOT NULL,
    periodo_letivo_id  BIGINT NOT NULL,

    CONSTRAINT uq_disponibilidade_prof_slot_periodo
        UNIQUE (
            professor_id,
            slot_id,
            periodo_letivo_id
        ),

    CONSTRAINT fk_disp_professor
        FOREIGN KEY (professor_id)
        REFERENCES professor (id),

    CONSTRAINT fk_disp_slot
        FOREIGN KEY (slot_id)
        REFERENCES slot (id),

    CONSTRAINT fk_disp_periodo_letivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES periodo_letivo (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 12. TABELA ALOCACAO
-- =====================================================================

CREATE TABLE alocacao (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    turma_id       BIGINT NOT NULL,
    disciplina_id  BIGINT NOT NULL,
    professor_id   BIGINT NOT NULL,
    aulas_semana   SMALLINT NOT NULL,

    CONSTRAINT uq_alocacao_turma_disciplina
        UNIQUE (
            turma_id,
            disciplina_id
        ),

    CONSTRAINT uq_alocacao_prof_turma
        UNIQUE (
            id,
            professor_id,
            turma_id
        ),

    CONSTRAINT fk_alocacao_turma
        FOREIGN KEY (turma_id)
        REFERENCES turma (id),

    CONSTRAINT fk_alocacao_disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES disciplina (id),

    CONSTRAINT fk_alocacao_professor
        FOREIGN KEY (professor_id)
        REFERENCES professor (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 13. TABELA PREFERENCIA_DISCIPLINA
-- =====================================================================

CREATE TABLE preferencia_disciplina (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    professor_id   BIGINT NOT NULL,
    disciplina_id  BIGINT NOT NULL,
    ordem          SMALLINT NOT NULL,

    CONSTRAINT uq_preferencia_professor_ordem
        UNIQUE (
            professor_id,
            ordem
        ),

    CONSTRAINT fk_pref_disc_professor
        FOREIGN KEY (professor_id)
        REFERENCES professor (id),

    CONSTRAINT fk_pref_disc_disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES disciplina (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 14. TABELA EXECUCAO_GERACAO
-- =====================================================================

CREATE TABLE execucao_geracao (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    periodo_letivo_id  BIGINT NOT NULL,
    solicitado_por     BIGINT NOT NULL,
    status             VARCHAR(20) NOT NULL,
    iniciada_em        DATETIME(6) NULL,
    concluida_em       DATETIME(6) NULL,
    algoritmo          VARCHAR(50) NULL,
    parametros         JSON NULL,
    violacoes_fracas   SMALLINT NULL,

    CONSTRAINT ck_execucao_status
        CHECK (
            status IN (
                'PENDENTE',
                'EM_EXECUCAO',
                'CONCLUIDA',
                'FALHA'
            )
        ),

    CONSTRAINT fk_execucao_periodo_letivo
        FOREIGN KEY (periodo_letivo_id)
        REFERENCES periodo_letivo (id),

    CONSTRAINT fk_execucao_usuario
        FOREIGN KEY (solicitado_por)
        REFERENCES usuario (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 15. TABELA AULA_AGENDADA
-- =====================================================================

CREATE TABLE aula_agendada (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    execucao_id   BIGINT NOT NULL,
    alocacao_id   BIGINT NOT NULL,
    slot_id       BIGINT NOT NULL,
    professor_id  BIGINT NOT NULL,
    turma_id      BIGINT NOT NULL,

    CONSTRAINT uq_aula_execucao_professor_slot
        UNIQUE (
            execucao_id,
            professor_id,
            slot_id
        ),

    CONSTRAINT uq_aula_execucao_turma_slot
        UNIQUE (
            execucao_id,
            turma_id,
            slot_id
        ),

    CONSTRAINT fk_aula_execucao
        FOREIGN KEY (execucao_id)
        REFERENCES execucao_geracao (id),

    CONSTRAINT fk_aula_slot
        FOREIGN KEY (slot_id)
        REFERENCES slot (id),

    CONSTRAINT fk_aula_alocacao
        FOREIGN KEY (
            alocacao_id,
            professor_id,
            turma_id
        )
        REFERENCES alocacao (
            id,
            professor_id,
            turma_id
        )
) ENGINE=InnoDB;


-- =====================================================================
-- 16. TABELA DIAGNOSTICO_INVIABILIDADE
-- =====================================================================

CREATE TABLE diagnostico_inviabilidade (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    execucao_id  BIGINT NOT NULL,
    tipo         VARCHAR(20) NOT NULL,
    mensagem     TEXT NOT NULL,

    CONSTRAINT ck_diagnostico_tipo
        CHECK (
            tipo IN (
                'DISPONIBILIDADE',
                'CONFLITO',
                'CAPACIDADE',
                'OUTRO'
            )
        ),

    CONSTRAINT fk_diagnostico_execucao
        FOREIGN KEY (execucao_id)
        REFERENCES execucao_geracao (id)
) ENGINE=InnoDB;


-- =====================================================================
-- 17. REGRA DE ADMINISTRADOR ÚNICO
-- =====================================================================
--
-- Apenas um usuário pode possuir papel ADMIN.
-- A coluna gerada transforma ADMIN em 1 e os demais em NULL.
-- Como existe UNIQUE, somente um valor 1 pode existir.
--
-- =====================================================================

ALTER TABLE usuario
    ADD COLUMN admin_unico TINYINT
    GENERATED ALWAYS AS (
        CASE
            WHEN papel = 'ADMIN' THEN 1
            ELSE NULL
        END
    ) STORED;

ALTER TABLE usuario
    ADD CONSTRAINT uq_admin_unico
    UNIQUE (admin_unico);


-- =====================================================================
-- 18. DADOS DE TESTE - USUARIOS
-- =====================================================================

INSERT INTO usuario (
    email,
    senha_hash,
    papel,
    ativo
) VALUES
(
    'admin@escola.com',
    '$2y$10$hashfake0000000000000000000000000000000000',
    'ADMIN',
    1
),
(
    'maria.silva@escola.com',
    '$2y$10$hashfake0000000000000000000000000000000001',
    'PROFESSOR',
    1
),
(
    'joao.souza@escola.com',
    '$2y$10$hashfake0000000000000000000000000000000002',
    'PROFESSOR',
    1
),
(
    'ana.lima@escola.com',
    '$2y$10$hashfake0000000000000000000000000000000003',
    'PROFESSOR',
    1
),
(
    'coordenador@escola.com',
    '$2y$10$hashfake0000000000000000000000000000000004',
    'COORDENADOR',
    1
);


-- =====================================================================
-- 19. DADOS DE TESTE - PROFESSORES
-- =====================================================================

INSERT INTO professor (
    usuario_id,
    matricula
) VALUES
(2, 'PROF001'),
(3, 'PROF002'),
(4, 'PROF003');


-- =====================================================================
-- 20. DADOS DE TESTE - PERIODOS LETIVOS
-- =====================================================================

INSERT INTO periodo_letivo (
    rotulo,
    data_inicio,
    data_fim,
    ativo
) VALUES
(
    '2026-1',
    '2026-02-02',
    '2026-06-30',
    1
);


-- =====================================================================
-- 21. DADOS DE TESTE - CURSOS
-- =====================================================================

INSERT INTO curso (
    nome,
    nivel_ensino
) VALUES
(
    'Ensino Fundamental II',
    'FUNDAMENTAL'
),
(
    'Ensino Médio',
    'MEDIO'
);


-- =====================================================================
-- 22. DADOS DE TESTE - DISCIPLINAS
-- =====================================================================

INSERT INTO disciplina (
    nome
) VALUES
('Matemática'),
('Português'),
('História');


-- =====================================================================
-- 23. DADOS DE TESTE - CURSO_DISCIPLINA
-- =====================================================================

INSERT INTO curso_disciplina (
    curso_id,
    disciplina_id,
    serie,
    aulas_semana
) VALUES
(1, 1, '9ANO',   5),
(1, 2, '9ANO',   4),
(2, 1, '1SERIE', 4),
(2, 3, '1SERIE', 3);


-- =====================================================================
-- 24. DADOS DE TESTE - TURMAS
-- =====================================================================

INSERT INTO turma (
    curso_id,
    periodo_letivo_id,
    serie,
    identificador,
    turno,
    qtd_alunos
) VALUES
(
    1,
    1,
    '9ANO',
    'A',
    'MANHA',
    30
),
(
    2,
    1,
    '1SERIE',
    'A',
    'TARDE',
    35
);


-- =====================================================================
-- 25. DADOS DE TESTE - PERIODOS DE AULA
-- =====================================================================

INSERT INTO periodo_aula (
    turno,
    ordem,
    hora_inicio,
    duracao_min
) VALUES
(
    'MANHA',
    1,
    '07:00:00',
    50
),
(
    'MANHA',
    2,
    '07:50:00',
    50
),
(
    'TARDE',
    1,
    '13:00:00',
    50
),
(
    'TARDE',
    2,
    '13:50:00',
    50
);


-- =====================================================================
-- 26. DADOS DE TESTE - SLOTS
-- =====================================================================

INSERT INTO slot (
    periodo_aula_id,
    dia_semana
) VALUES
(1, 'SEG'),
(1, 'TER'),
(1, 'QUA'),
(2, 'SEG'),
(2, 'TER'),
(3, 'SEG'),
(3, 'QUA'),
(4, 'SEG');


-- =====================================================================
-- 27. PROFESSOR x DISCIPLINA
-- =====================================================================

INSERT INTO professor_disciplina (
    professor_id,
    disciplina_id
) VALUES
(1, 1),
(2, 2),
(3, 3);


-- =====================================================================
-- 28. DISPONIBILIDADE DOS PROFESSORES
-- =====================================================================

INSERT INTO disponibilidade (
    professor_id,
    slot_id,
    periodo_letivo_id
) VALUES
(1, 1, 1),
(1, 2, 1),
(1, 3, 1),
(1, 4, 1),
(1, 5, 1),

(2, 1, 1),
(2, 2, 1),
(2, 4, 1),
(2, 5, 1),

(3, 6, 1),
(3, 7, 1),
(3, 8, 1);


-- =====================================================================
-- 29. ALOCAÇÕES
-- =====================================================================

INSERT INTO alocacao (
    turma_id,
    disciplina_id,
    professor_id,
    aulas_semana
) VALUES
(
    1,
    1,
    1,
    5
),
(
    1,
    2,
    2,
    4
),
(
    2,
    1,
    1,
    4
),
(
    2,
    3,
    3,
    3
);


-- =====================================================================
-- 30. PREFERÊNCIAS DOS PROFESSORES
-- =====================================================================

INSERT INTO preferencia_disciplina (
    professor_id,
    disciplina_id,
    ordem
) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 3, 1);


-- =====================================================================
-- 31. EXECUÇÕES DO ALGORITMO
-- =====================================================================

INSERT INTO execucao_geracao (
    periodo_letivo_id,
    solicitado_por,
    status,
    iniciada_em,
    concluida_em,
    algoritmo,
    parametros,
    violacoes_fracas
) VALUES
(
    1,
    1,
    'CONCLUIDA',
    '2026-01-20 08:00:00.000000',
    '2026-01-20 08:00:12.500000',
    'BACKTRACKING',
    JSON_OBJECT('max_iter', 1000),
    2
),
(
    1,
    5,
    'FALHA',
    '2026-01-21 09:00:00.000000',
    NULL,
    'BACKTRACKING',
    JSON_OBJECT('max_iter', 500),
    NULL
);


-- =====================================================================
-- 32. AULAS AGENDADAS
-- =====================================================================

INSERT INTO aula_agendada (
    execucao_id,
    alocacao_id,
    slot_id,
    professor_id,
    turma_id
) VALUES
(1, 1, 1, 1, 1),
(1, 1, 2, 1, 1),
(1, 2, 4, 2, 1),
(1, 3, 6, 1, 2),
(1, 4, 7, 3, 2);


-- =====================================================================
-- 33. DIAGNÓSTICOS DE INVIABILIDADE
-- =====================================================================

INSERT INTO diagnostico_inviabilidade (
    execucao_id,
    tipo,
    mensagem
) VALUES
(
    2,
    'DISPONIBILIDADE',
    'Professor Ana Lima nao possui disponibilidade suficiente para atender a carga horaria de Historia na turma 1a Serie A.'
),
(
    2,
    'CONFLITO',
    'Conflito detectado entre duas alocacoes da turma 1a Serie A no mesmo slot.'
);


-- =====================================================================
-- CONSULTAS
-- =====================================================================


-- =====================================================================
-- CONSULTA 1
-- Carga horária x disponibilidade por professor
-- =====================================================================

SELECT
    p.id AS professor_id,
    u.email,
    p.matricula,

    COALESCE(al.total_alocado, 0) AS total_alocado,

    COALESCE(disp.total_disponivel, 0) AS total_disponivel,

    CASE
        WHEN COALESCE(al.total_alocado, 0)
             >
             COALESCE(disp.total_disponivel, 0)
        THEN 'RISCO DE SOBRECARGA'

        ELSE 'OK'
    END AS indicador

FROM professor p

JOIN usuario u
    ON u.id = p.usuario_id

LEFT JOIN (
    SELECT
        professor_id,
        SUM(aulas_semana) AS total_alocado

    FROM alocacao

    GROUP BY professor_id
) al
    ON al.professor_id = p.id

LEFT JOIN (
    SELECT
        professor_id,
        COUNT(*) AS total_disponivel

    FROM disponibilidade

    WHERE periodo_letivo_id = 1

    GROUP BY professor_id
) disp
    ON disp.professor_id = p.id;


-- =====================================================================
-- CONSULTA 2
-- Grade horária completa de uma turma
-- =====================================================================

SELECT
    s.dia_semana,
    pa.hora_inicio,
    d.nome AS disciplina,
    u.email AS professor

FROM aula_agendada aa

JOIN alocacao al
    ON al.id = aa.alocacao_id

JOIN disciplina d
    ON d.id = al.disciplina_id

JOIN professor p
    ON p.id = aa.professor_id

JOIN usuario u
    ON u.id = p.usuario_id

JOIN slot s
    ON s.id = aa.slot_id

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

WHERE aa.execucao_id = 1
  AND aa.turma_id = 2

ORDER BY
    FIELD(
        s.dia_semana,
        'SEG',
        'TER',
        'QUA',
        'QUI',
        'SEX',
        'SAB'
    ),
    pa.hora_inicio;


-- =====================================================================
-- CONSULTA 3
-- Cobertura curricular
-- =====================================================================

SELECT
    c.nome AS curso,
    cd.serie,
    d.nome AS disciplina

FROM curso_disciplina cd

JOIN curso c
    ON c.id = cd.curso_id

JOIN disciplina d
    ON d.id = cd.disciplina_id

JOIN turma t
    ON t.curso_id = cd.curso_id
    AND t.serie = cd.serie

LEFT JOIN alocacao al
    ON al.turma_id = t.id
    AND al.disciplina_id = cd.disciplina_id

WHERE al.id IS NULL;


-- =====================================================================
-- CONSULTA 4
-- Comparação entre execuções
-- =====================================================================

SELECT
    eg.id AS execucao_id,
    eg.status,

    COUNT(DISTINCT aa.id) AS total_aulas_agendadas,

    COUNT(DISTINCT di.id) AS total_diagnosticos

FROM execucao_geracao eg

LEFT JOIN aula_agendada aa
    ON aa.execucao_id = eg.id

LEFT JOIN diagnostico_inviabilidade di
    ON di.execucao_id = eg.id

WHERE eg.periodo_letivo_id = 1

GROUP BY
    eg.id,
    eg.status;


-- =====================================================================
-- CONSULTA 5
-- Ociosidade de slots por turno
-- =====================================================================

SELECT
    pa.turno,
    COUNT(*) AS slots_ociosos

FROM slot s

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

LEFT JOIN aula_agendada aa
    ON aa.slot_id = s.id
    AND aa.execucao_id = 1

WHERE aa.id IS NULL

GROUP BY pa.turno;


-- =====================================================================
-- CONSULTA 6
-- Grade horária da turma 1
-- =====================================================================

SELECT
    s.dia_semana,
    pa.hora_inicio,
    d.nome AS disciplina,
    u.email AS professor

FROM aula_agendada aa

JOIN alocacao al
    ON al.id = aa.alocacao_id

JOIN disciplina d
    ON d.id = al.disciplina_id

JOIN professor p
    ON p.id = aa.professor_id

JOIN usuario u
    ON u.id = p.usuario_id

JOIN slot s
    ON s.id = aa.slot_id

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

WHERE aa.turma_id = 1
  AND aa.execucao_id = 1

ORDER BY
    FIELD(
        s.dia_semana,
        'SEG',
        'TER',
        'QUA',
        'QUI',
        'SEX',
        'SAB'
    ),
    pa.hora_inicio;


-- =====================================================================
-- CONSULTA 7
-- Aulas de um professor
-- =====================================================================

SELECT
    s.dia_semana,
    pa.hora_inicio,
    t.serie,
    t.identificador,
    d.nome AS disciplina

FROM aula_agendada aa

JOIN alocacao al
    ON al.id = aa.alocacao_id

JOIN disciplina d
    ON d.id = al.disciplina_id

JOIN turma t
    ON t.id = aa.turma_id

JOIN slot s
    ON s.id = aa.slot_id

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

WHERE aa.professor_id = 1
  AND aa.execucao_id = 1

ORDER BY
    FIELD(
        s.dia_semana,
        'SEG',
        'TER',
        'QUA',
        'QUI',
        'SEX',
        'SAB'
    ),
    pa.hora_inicio;


-- =====================================================================
-- CONSULTA 8
-- Disciplinas de um curso
-- =====================================================================

SELECT
    cd.serie,
    d.nome AS disciplina,
    cd.aulas_semana

FROM curso_disciplina cd

JOIN disciplina d
    ON d.id = cd.disciplina_id

WHERE cd.curso_id = 1

ORDER BY
    cd.serie,
    d.nome;


-- =====================================================================
-- CONSULTA 9
-- Disponibilidade de um professor
-- =====================================================================

SELECT
    s.dia_semana,
    pa.hora_inicio,
    disp.periodo_letivo_id

FROM disponibilidade disp

JOIN slot s
    ON s.id = disp.slot_id

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

WHERE disp.professor_id = 1

ORDER BY
    FIELD(
        s.dia_semana,
        'SEG',
        'TER',
        'QUA',
        'QUI',
        'SEX',
        'SAB'
    ),
    pa.hora_inicio;


-- =====================================================================
-- CONSULTA 10
-- Todas as aulas agendadas
-- =====================================================================

SELECT
    aa.id,
    t.serie,
    t.identificador,
    d.nome AS disciplina,
    u.email AS professor,
    s.dia_semana,
    pa.hora_inicio

FROM aula_agendada aa

JOIN turma t
    ON t.id = aa.turma_id

JOIN alocacao al
    ON al.id = aa.alocacao_id

JOIN disciplina d
    ON d.id = al.disciplina_id

JOIN professor p
    ON p.id = aa.professor_id

JOIN usuario u
    ON u.id = p.usuario_id

JOIN slot s
    ON s.id = aa.slot_id

JOIN periodo_aula pa
    ON pa.id = s.periodo_aula_id

WHERE aa.execucao_id = 1;


-- =====================================================================
-- CONSULTA 11
-- Professores e suas disciplinas
-- =====================================================================

SELECT
    u.email,
    p.matricula,
    d.nome AS disciplina

FROM professor p

JOIN usuario u
    ON u.id = p.usuario_id

JOIN professor_disciplina pd
    ON pd.professor_id = p.id

JOIN disciplina d
    ON d.id = pd.disciplina_id

ORDER BY
    u.email;


-- =====================================================================
-- CONSULTA 12
-- Quantidade de aulas por professor
-- =====================================================================

SELECT
    u.email,
    COUNT(*) AS total_aulas

FROM aula_agendada aa

JOIN professor p
    ON p.id = aa.professor_id

JOIN usuario u
    ON u.id = p.usuario_id

WHERE aa.execucao_id = 1

GROUP BY
    u.email;


-- =====================================================================
-- CONSULTA 13
-- Quantidade de aulas por turma
-- =====================================================================

SELECT
    t.serie,
    t.identificador,
    COUNT(*) AS total_aulas

FROM aula_agendada aa

JOIN turma t
    ON t.id = aa.turma_id

WHERE aa.execucao_id = 1

GROUP BY
    t.serie,
    t.identificador;


-- =====================================================================
-- CONSULTA 14
-- Identificar conflitos de professor no mesmo slot
-- =====================================================================

SELECT
    execucao_id,
    professor_id,
    slot_id,
    COUNT(*) AS ocorrencias

FROM aula_agendada

GROUP BY
    execucao_id,
    professor_id,
    slot_id

HAVING COUNT(*) > 1;


-- =====================================================================
-- CONSULTA 15
-- Diagnósticos de uma execução
-- =====================================================================

SELECT
    tipo,
    mensagem

FROM diagnostico_inviabilidade

WHERE execucao_id = 2;


-- =====================================================================
-- CONSULTA 16
-- Listar todos os usuários
-- =====================================================================

SELECT
    id,
    email,
    papel,
    ativo

FROM usuario
ORDER BY id;


-- =====================================================================
-- CONSULTA 17
-- Listar professores
-- =====================================================================

SELECT
    p.id,
    u.email,
    p.matricula

FROM professor p

JOIN usuario u
    ON u.id = p.usuario_id

ORDER BY p.id;


-- =====================================================================
-- CONSULTA 18
-- Listar turmas
-- =====================================================================

SELECT
    t.id,
    c.nome AS curso,
    t.serie,
    t.identificador,
    t.turno,
    t.qtd_alunos,
    pl.rotulo AS periodo_letivo

FROM turma t

JOIN curso c
    ON c.id = t.curso_id

JOIN periodo_letivo pl
    ON pl.id = t.periodo_letivo_id

ORDER BY
    t.id;


-- =====================================================================
-- CONSULTA 19
-- Listar todas as disciplinas
-- =====================================================================

SELECT
    id,
    nome

FROM disciplina
ORDER BY id;


-- =====================================================================
-- CONSULTA 20
-- Listar execuções do algoritmo
-- =====================================================================

SELECT
    eg.id,
    pl.rotulo AS periodo_letivo,
    u.email AS solicitado_por,
    eg.status,
    eg.iniciada_em,
    eg.concluida_em,
    eg.algoritmo,
    eg.parametros,
    eg.violacoes_fracas

FROM execucao_geracao eg

JOIN periodo_letivo pl
    ON pl.id = eg.periodo_letivo_id

JOIN usuario u
    ON u.id = eg.solicitado_por

ORDER BY
    eg.id;


-- =====================================================================
-- FIM DO SCRIPT PRINCIPAL
-- =====================================================================


-- =====================================================================
-- TESTES DE INTEGRIDADE
-- =====================================================================
--
-- ESTES COMANDOS DEVEM SER EXECUTADOS INDIVIDUALMENTE.
-- Eles foram mantidos aqui como referência, mas estão comentados
-- para que o script principal execute sem ser interrompido por erros.
--
-- =====================================================================


-- TESTE 1 - Tentar cadastrar segundo administrador
--
-- Deve gerar erro por causa de uq_admin_unico.
--
-- INSERT INTO usuario (
--     email,
--     senha_hash,
--     papel,
--     ativo
-- )
-- VALUES (
--     'outro.admin@escola.com',
--     '$2y$10$hashfake9999999999999999999999999999999999',
--     'ADMIN',
--     1
-- );


-- TESTE 2 - Tentar cadastrar slot duplicado
--
-- Deve gerar erro por causa de uq_slot_periodo_dia.
--
-- INSERT INTO slot (
--     periodo_aula_id,
--     dia_semana
-- )
-- VALUES (
--     1,
--     'SEG'
-- );


-- TESTE 3 - Tentar cadastrar turma duplicada
--
-- Deve gerar erro por causa de uq_turma_curso_periodo_serie_id.
--
-- INSERT INTO turma (
--     curso_id,
--     periodo_letivo_id,
--     serie,
--     identificador,
--     turno,
--     qtd_alunos
-- )
-- VALUES (
--     1,
--     1,
--     '9ANO',
--     'A',
--     'MANHA',
--     28
-- );


-- TESTE 4 - Tentar alocar disciplina para professor incorreto
--
-- Dependendo dos dados e da regra desejada, este teste deve ser
-- complementado com uma regra de integridade específica.
--
-- INSERT INTO alocacao (
--     turma_id,
--     disciplina_id,
--     professor_id,
--     aulas_semana
-- )
-- VALUES (
--     1,
--     1,
--     2,
--     3
-- );


-- TESTE 5 - Tentar cadastrar aula com combinação inválida
--
-- A FK composta de aula_agendada deve impedir que professor/turma
-- não correspondam à alocação.
--
-- INSERT INTO aula_agendada (
--     execucao_id,
--     alocacao_id,
--     slot_id,
--     professor_id,
--     turma_id
-- )
-- VALUES (
--     1,
--     3,
--     1,
--     1,
--     2
-- );


-- TESTE 6 - Conflito de professor no mesmo slot
--
-- Deve gerar erro por causa de:
-- uq_aula_execucao_professor_slot
--
-- INSERT INTO aula_agendada (
--     execucao_id,
--     alocacao_id,
--     slot_id,
--     professor_id,
--     turma_id
-- )
-- VALUES (
--     1,
--     2,
--     1,
--     2,
--     1
-- );


-- TESTE 7 - Sobreposição de horário
--
-- Este teste depende do trigger de sobreposição.
-- Como o trigger não está no script principal, ele não será executado aqui.
--
-- INSERT INTO periodo_aula (
--     turno,
--     ordem,
--     hora_inicio,
--     duracao_min
-- )
-- VALUES (
--     'MANHA',
--     3,
--     '07:20:00',
--     40
-- );


-- TESTE 8 - Tentar excluir uma execução
--
-- Este teste depende do trigger de preservação de histórico.
--
-- DELETE FROM execucao_geracao
-- WHERE id = 2;


-- =====================================================================
-- FIM
-- =====================================================================
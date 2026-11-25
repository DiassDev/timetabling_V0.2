## Objetivo geral do sistema

Desenvolver um motor matemático em python utilizando as seguintes heurísticas: Simulated Anniling e Algoritmo genético. 
O algoritmo será utilizado em um sistema timetabling ( alocação de horários ) e deverá respeitar os requisitos especificados no documento ./requisitostimetabling.pdf ( leia-o antes de qualquer iteração de código ).

Tenha em mente que estamos desenvolvendo esse motor de maneira isolada, para fins de testes no qual posteriormente ele será integrado em um outro sistema, então utilizaremos dados de testes, próximos do que precisamos, mas ainda assim simulados.

### Task - Criação do algoritmo utilizando simulated anniling + algoritmo genético

Desenvolva um motor matemático em python utilizando as duas técnicas de heurísticas. Utilizaremos uma abordagem pragmática, utilizando os conceitos NSR, Ortogonalidade e abstração quando aplicáveis. Certifique-se de comentar as funcionalidades de maneira geral, dispensando explicações detalhadas, apenas um guia prático do que cada função faz, sem necessáriamente explicar cada linha, isto porque, o código deve ser autoexplicado o suficiente, senão for, já ferimos o princípio de legibilidade que queremos alcançar. NÃO implemente nada além do especificado.

### Task - Criação da camada backend e modelagem de banco de dados em django

Desenvolva um backend em django, utilizando sqlite3. Preciso que siga exatamente a modelagem ( arquivo.sql que deverá ser implementado em sqlite3, armazenado em ./docs/queries.sql ). Começaremos modelando o banco em models, leve em conta que devemos utilizar princípios de boas práticas ao criá-lo, como atomicidade e padrões ACID. Crie esse banco de dados já preparado para se comunicar com o frontend via API Rest ( utilize restframework do próprio django, ambos django e restframework já estão instalados ). Utilize uma abordagem pragmática, já mencionada na task anterior.

### Task - Criação das telas do front-end em React + TypeScript

O front-end deve ser feito em React com TypeScript, integrado ao backend Django REST Framework. Os requisitos de domínio e comportamento abaixo seguem `docs/requisitostimetabling.pdf`; escolhas de cores, tipografia, organização visual e componentes são decisões da equipe.

#### Requisitos de interface por fluxo

- **Acesso e papéis:** prever login, recuperação de senha e experiências distintas para Admin, Coordenador e Professor. Deve existir um único Admin, que cadastra coordenadores. O coordenador administra estrutura, slots, alocações, geração e exportação; o professor declara disponibilidade. A interface deve refletir as permissões do usuário autenticado.
- **Visão geral:** resumir período letivo, alocações completas e pendentes, disponibilidade, estado da última geração e conflitos/inviabilidades em linguagem compreensível.
- **Horários:** exibir grade por dia e slot, com filtros de período letivo, turno, curso/turma e professor; permitir ao coordenador revisar o resultado, visualizar a versão publicada e exportar a grade.
- **Slots de horário:** permitir configurar dias ativos, horário de início e duração de cada slot; impedir sobreposição entre slots.
- **Estrutura acadêmica:** cadastrar cursos (nome e nível), turmas (série, curso, quantidade de alunos, período letivo e turno), disciplinas e professores. Permitir várias turmas por curso, associação de disciplinas a cursos/séries e relação N:N entre professores e disciplinas.
- **Disponibilidade:** permitir ao professor cadastrar e alterar os dias e horários em que pode lecionar, limitados aos slots existentes e ao período letivo; não oferecer escolha de disciplina ou turma nesse fluxo.
- **Alocações:** permitir ao coordenador definir professor, disciplina, turma e carga horária semanal antes da geração. Alocações são entradas humanas e não podem ser criadas ou alteradas pelo algoritmo.
- **Geração automática:** executar a cada solicitação a partir do zero. Validar viabilidade antes de executar e explicar inviabilidade com causa de domínio. As restrições fortes são bloqueantes: não repetir professor no mesmo slot, respeitar disponibilidade e manter no máximo uma alocação por professor/turma/slot. Minimizar janelas vagas para professor e turma e considerar a preferência ordinal opcional por disciplinas como restrições fracas. A decisão de quem leciona o quê continua humana; o gerador decide apenas quando.
- **Resultado e exportação:** permitir revisar e disponibilizar o horário final aos professores sem decisões de alocação por parte deles; exportar como tabela/planilha agrupada por dia/horário, professor e disciplina, com agrupamento de turmas compatíveis.
- **Acessibilidade e operação:** aplicação web utilizável remotamente pelo navegador, com mensagens de erro em linguagem não técnica e suporte à escala de referência de 50 professores, 11 a 14 turmas por turno.

#### Implementação inicial

O diretório `frontend/` contém a interface em Vite, React e TypeScript, com página inicial de acesso, painel, grade semanal, alocações, disponibilidade, estrutura acadêmica, horários-base e gestão de usuários. Os cadastros e ações desta versão são funcionais e ficam salvos no navegador; a geração do motor e a integração com o banco seguem como etapas pendentes.

A API disponível está em `/api/` e expõe recursos como `usuarios`, `professores`, `disciplinas`, `periodos-letivos`, `cursos`, `turmas`, `periodos-aula`, `slots`, `disponibilidades`, `alocacoes`, `execucoes`, `aulas-agendadas` e `diagnosticos`. Continuam pendentes a integração efetiva desses endpoints, autenticação/autorização no servidor, sincronização entre dispositivos, recuperação automática de senha e chamada real à geração do motor.

Para executar a interface localmente: `cd frontend`, `npm install` e `npm run dev`. Para compilar: `npm run build`.

### Atualização das telas e regras de acesso

- A primeira página do sistema é o acesso. Na primeira abertura, ela permite cadastrar o administrador inicial; depois, cada pessoa entra com e-mail, senha e perfil. O administrador pode criar acessos de coordenador e professor, e permanece único.
- O perfil **Administrador** é o único que pode criar, editar ou remover horários-base. **Coordenador** pode cadastrar cursos, turmas, matérias e aulas. **Professor** consulta a grade e mantém apenas a própria disponibilidade.
- O cadastro de aula solicita horário, matéria, professor, turma e aulas por semana. O cadastro de disponibilidade permite selecionar horários-base já cadastrados. Os formulários validam campos obrigatórios e horários sobrepostos.
- As telas de horários, cadastros, alocações, disponibilidade e usuários têm ações de inclusão, edição ou remoção de acordo com o perfil. A grade pode ser baixada como arquivo CSV.
- Nesta versão, os acessos e registros são guardados no navegador usado para abrir o sistema. A autenticação e autorização ainda não estão ligadas ao banco Django; os dados não são compartilhados automaticamente entre navegadores ou computadores. A geração automática do motor ainda não foi conectada à interface.
- Os formulários usam textos voltados à equipe escolar, sem instruções de integração ou detalhes internos do sistema.
- O login apresenta as três opções de perfil lado a lado. Após a entrada, a página inicial é a grade semanal; ela mostra as aulas por dia e horário, e para professores exibe somente suas próprias aulas.
- A grade semanal sempre reserva linhas de horários e colunas dos dias úteis, mesmo antes dos primeiros cadastros, evitando a impressão de página vazia. Mensagens de acesso distinguem e-mail desconhecido, senha incorreta e perfil selecionado diferente do perfil cadastrado.
- Na área **Usuários** do administrador, há formulários separados para cadastrar professor e coordenador. Após o cadastro, cada pessoa pode entrar com seu perfil e acessar a grade principal. O administrador continua sendo o único perfil autorizado a manter horários-base.
- A configuração do primeiro administrador permanece disponível enquanto ainda não existir um perfil administrador, mesmo que já haja contas antigas de professor ou coordenador. Isso evita bloquear a configuração da escola por causa de cadastros anteriores.
- Registros antigos ou incompletos do navegador são tratados antes de montar as telas. Uma falha inesperada de renderização apresenta uma ação para voltar ao acesso em vez de deixar uma página em branco.
- A grade após o acesso mantém a mesma ordem de hooks do React entre a tela de login e as telas internas; o cadastro e a entrada não devem interromper a abertura da grade.
- A navegação interna permite voltar à tela anterior. Na área de usuários do administrador, a opção **Recomeçar do zero** pede confirmação e apaga acessos e registros guardados neste navegador, retornando ao cadastro inicial do administrador.
- O servidor tenta iniciar em `http://localhost:5173`. Se essa porta estiver ocupada, ele inicia automaticamente na próxima porta livre e informa o endereço no terminal. Acesse sempre o endereço mostrado pelo Vite; os dados salvos no navegador são separados por endereço. Inicie com `npm run dev` dentro de `frontend`; não use a visualização estática do editor para abrir esta aplicação React.
### Task - Criar tela de disponibilidade de professores

- A tela **Disponibilidade** mostra uma grade semanal (dias úteis × horários-base) separada por turno (Manhã, Tarde, Noite).
- O professor clica em cada horário para marcar ou desmarcar a disponibilidade. Também pode marcar ou limpar o turno inteiro. As alterações são salvas na hora e valem só para a própria disponibilidade. Não há escolha de disciplina nem de turma.
- A coordenação escolhe um professor e consulta a disponibilidade dele, sem poder editar.
- Sem horários-base cadastrados, a tela pede ao administrador que os cadastre.


### Integração do frontend com a API

- Todas as telas (acesso, visão geral, horários, alocações, disponibilidade, estrutura acadêmica, slots e usuários) leem e gravam no banco Django pela API. No navegador fica guardada apenas a sessão de quem entrou.
- Endpoints usados pelas telas, em `/api/ui/`: `estado/` (todos os dados do período letivo ativo e a última geração), `login/`, `contas/`, `registros/<seção>/` (incluir, editar e remover) e `disponibilidade/` (substitui os horários disponíveis de um professor).
- A geração usa `/api/execucoes/gerar/` com o período letivo ativo e o usuário que solicitou. O resultado fica salvo no banco e volta a aparecer ao abrir o sistema.
- O nome exibido de cada usuário vem do e-mail, porque o modelo de dados não tem campo de nome. **Recomeçar do zero** limpa só o navegador; os cadastros no banco são mantidos.
- Para executar: `.\venv\Scripts\python.exe manage.py runserver` e, em outro terminal, `npm run dev` dentro de `frontend` (o Vite repassa `/api` para a porta 8000).


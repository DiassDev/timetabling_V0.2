## Objetivo geral do sistema

Desenvolver um motor matemático em python utilizando as seguintes heurísticas: Simulated Anniling e Algoritmo genético. 
O algoritmo será utilizado em um sistema timetabling ( alocação de horários ) e deverá respeitar os requisitos especificados no documento ./requisitostimetabling.pdf ( leia-o antes de qualquer iteração de código ).

Tenha em mente que estamos desenvolvendo esse motor de maneira isolada, para fins de testes no qual posteriormente ele será integrado em um outro sistema, então utilizaremos dados de testes, próximos do que precisamos, mas ainda assim simulados.

### Task - Criação do algoritmo utilizando simulated anniling + algoritmo genético

Desenvolva um motor matemático em python utilizando as duas técnicas de heurísticas. Utilizaremos uma abordagem pragmática, utilizando os conceitos NSR, Ortogonalidade e abstração quando aplicáveis. Certifique-se de comentar as funcionalidades de maneira geral, dispensando explicações detalhadas, apenas um guia prático do que cada função faz, sem necessáriamente explicar cada linha, isto porque, o código deve ser autoexplicado o suficiente, senão for, já ferimos o princípio de legibilidade que queremos alcançar. NÃO implemente nada além do especificado.

### Task - Criação da camada backend e modelagem de banco de dados em django

Desenvolva um backend em django, utilizando sqlite3. Preciso que siga exatamente a modelagem ( arquivo.sql que deverá ser implementado em sqlite3, armazenado em ./docs/queries.sql ). Começaremos modelando o banco em models, leve em conta que devemos utilizar princípios de boas práticas ao criá-lo, como atomicidade e padrões ACID. Crie esse banco de dados já preparado para se comunicar com o frontend via API Rest ( utilize restframework do próprio django, ambos django e restframework já estão instalados ). Utilize uma abordagem pragmática, já mencionada na task anterior.
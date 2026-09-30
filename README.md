# Análise de Dados de uma Operação de Delivery

## Sobre o projeto

Este projeto apresenta uma análise exploratória de dados de uma operação de delivery. O objetivo é transformar planilhas operacionais em informações que apoiem decisões sobre vendas, eficiência da operação e retenção de clientes.

Os dados utilizados incluem pedidos, histórico de clientes e avaliações. Como as bases possuem informações pessoais, os arquivos brutos não são enviados ao Git e não devem ser publicados.

## Problema de negócio

Uma operação de delivery precisa crescer sem comprometer sua capacidade de atendimento. Para isso, é necessário responder perguntas como:

- Em quais dias e horários a demanda é maior?
- Como os pedidos se distribuem por status, origem e forma de pagamento?
- Qual é o ticket médio dos pedidos concluídos?
- O tempo de preparo está dentro de uma faixa razoável?
- Existe oportunidade de reativar clientes inativos?

## Metodologia

O case segue as etapas do **CRISP-DM**, uma metodologia comum em projetos de ciência de dados:

1. **Entendimento do negócio:** definir decisões que a análise deve apoiar.
2. **Entendimento dos dados:** conhecer as planilhas, suas colunas e limitações.
3. **Preparação dos dados:** converter datas, selecionar campos e criar variáveis analíticas.
4. **Análise:** calcular indicadores, agrupar pedidos e identificar padrões.
5. **Avaliação:** validar resultados e registrar problemas de qualidade dos dados.
6. **Entrega:** gerar gráficos, tabelas tratadas e relatório automático.

## Indicadores calculados

- Total de pedidos
- Pedidos concluídos e taxa de conclusão
- Faturamento registrado e faturamento de pedidos concluídos
- Ticket médio
- Tempo mediano entre aceite e preparo
- Pedidos por mês, semana e dia
- Filtros de período e comparação entre dois intervalos
- Pedidos por dia da semana e hora
- Pedidos por status e forma de pagamento
- Segmentação de clientes por classificação do sistema
- Segmentação RFM por recência, frequência e valor histórico
- Registros com duração final inconsistente

## Estrutura do projeto

```text
Analise_Veneza/
├── dados/
│   ├── brutos/              # Planilhas originais do cliente
│   ├── tratados/            # Arquivos gerados pelo código
│   └── publicos/            # Agregações seguras para o dashboard
├── dashboard/
│   └── app.py               # Dashboard interativo em Streamlit
├── documentacao/            # Dicionário e decisões metodológicas
├── imagens/                 # Gráficos gerados pela análise
├── notebooks/               # Explorações futuras em Jupyter
├── relatorios/
│   └── gerados/             # Relatório automático local
├── src/
│   ├── carga.py             # Leitura dos arquivos
│   ├── tratamento.py        # Limpeza e criação de variáveis
│   ├── analise.py           # Indicadores e agregações
│   ├── visualizacao.py      # Geração dos gráficos
│   └── relatorio.py         # Relatório em Markdown
├── testes/                  # Testes automatizados futuros
├── main.py                  # Executa o fluxo completo
├── requirements.txt         # Dependências do projeto
└── README.md
```

## Como executar

No terminal do PyCharm, com a `.venv` ativada:

```powershell
pip install -r requirements.txt
python main.py
```

Ao final da execução, o projeto gera:

- Bases tratadas em `dados/tratados/`
- Cinco gráficos em `imagens/geradas/`
- Um relatório em `relatorios/gerados/relatorio_analitico.md`
- Dados públicos agregados em `dados/publicos/`

## Dashboard interativo

Depois de executar `main.py`, abra o dashboard com:

```powershell
streamlit run dashboard/app.py
```

O dashboard permite analisar os dados mês a mês, semana a semana ou dia a dia. Também permite selecionar um intervalo de datas e comparar dois períodos por pedidos, taxa de conclusão e índice de faturamento. Os valores financeiros aparecem como índice, e não em reais, para reduzir a exposição de informações comerciais.

## Segmentação RFM

RFM é uma técnica de segmentação de clientes baseada em:

- **Recência:** há quanto tempo o cliente não compra;
- **Frequência:** quantos pedidos já realizou;
- **Valor monetário:** quanto já faturou historicamente.

O projeto classifica os clientes em cinco grupos: clientes fiéis, clientes recentes, clientes em risco, baixo engajamento e oportunidade. A finalidade é apoiar campanhas de retenção e reativação, não fazer contato automático com clientes.

## Avaliações

O PDF de avaliações foi auditado, mas é uma impressão visual sem texto estruturado. Por isso, o projeto registra essa limitação no relatório. Para uma análise de sentimentos confiável, o próximo insumo necessário é uma exportação de avaliações em CSV ou XLSX, ou uma etapa de OCR revisada manualmente.

## Cuidados com os dados

As planilhas brutas possuem nomes, telefones, endereços, identificadores e coordenadas. Por isso:

- `dados/brutos/` e `dados/tratados/` estão no `.gitignore`.
- Não publique planilhas, capturas de tela com dados pessoais ou relatórios com identificação de clientes.
- Para o portfólio público, use números agregados, dados anonimizados ou uma base fictícia com a mesma estrutura.

## Principais limitações encontradas

- Alguns status de entrega possuem registros de tempo muito acima do plausível. O projeto marca durações fora de 0 a 180 minutos como inconsistentes.
- A base de clientes é um retrato histórico e não deve ser tratada como uma correspondência completa com os pedidos do período analisado.
- Não há itens do pedido ou custos dos produtos, então ainda não é possível analisar margem, produtos mais vendidos ou rentabilidade por item.

## Próximas evoluções

- Criar um notebook para análises mais detalhadas.
- Incluir dados de produtos e custos para análise de margem.
- Adicionar testes para validar regras de tratamento e métricas.

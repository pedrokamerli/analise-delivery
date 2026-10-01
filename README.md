# Análise de Dados de uma Operação de Delivery

Este é um projeto que desenvolvi para praticar um fluxo de análise de dados de ponta a ponta. Parti de planilhas reais de uma operação de delivery e organizei os dados para responder perguntas sobre demanda, eficiência operacional e comportamento de compra.

Por se tratar de dados de cliente, as planilhas originais e qualquer informação identificável ficam fora deste repositório. Aqui publico somente o código, a documentação e bases agregadas que permitem reproduzir o dashboard sem expor informações pessoais ou comerciais.

## O que eu quis responder

Durante a análise, busquei entender principalmente:

- Em quais dias e horários a demanda é maior?
- Qual é a taxa de conclusão dos pedidos?
- Como os pedidos se comportam ao longo do mês, da semana e do dia?
- Há mudanças relevantes ao comparar dois períodos?
- Como está o tempo de preparo da operação?
- Quais grupos de clientes merecem ações de retenção ou reativação?

## Como conduzi a análise

Usei o CRISP-DM como referência para estruturar o case: comecei pelo entendimento das perguntas de negócio, explorei as planilhas, tratei datas e campos necessários, criei indicadores e, por fim, transformei os resultados em gráficos, relatório e dashboard.

Também fiz uma auditoria do arquivo de avaliações. Como ele foi exportado como PDF visual, sem texto estruturado, registrei essa limitação em vez de tentar inferir sentimentos sem uma base confiável.

## Principais entregas

- Indicadores de pedidos, conclusão, ticket médio e tempo de preparo;
- Análises por mês, semana, data, dia da semana, hora, status e forma de pagamento;
- Comparação entre dois intervalos selecionados;
- Segmentação RFM de clientes por recência, frequência e valor histórico;
- Dashboard interativo construído com Streamlit;
- Relatório automático e gráficos para apoiar a interpretação dos resultados.

## Tecnologias utilizadas

Python, Pandas, Plotly, Matplotlib, Seaborn, Streamlit, PyPDF e Pytest.

## Estrutura do projeto

```text
Analise_Veneza/
├── dados/
│   ├── brutos/              # Arquivos originais, ignorados pelo Git
│   ├── tratados/            # Arquivos locais gerados no tratamento
│   └── publicos/            # Agregações seguras usadas no dashboard
├── dashboard/
│   └── app.py               # Dashboard Streamlit
├── documentacao/            # Narrativa e decisões do case
├── imagens/                 # Gráficos gerados pela análise
├── relatorios/              # Relatório automático local
├── src/                     # Módulos de carga, tratamento e análise
├── testes/                  # Testes automatizados
├── main.py                  # Executa o fluxo completo
└── requirements.txt         # Dependências
```

## Como executar

No terminal do PyCharm, com o ambiente virtual ativado:

```powershell
pip install -r requirements.txt
python main.py
```

Esse comando gera as bases tratadas localmente, os gráficos, o relatório e as agregações públicas usadas pelo dashboard.

Para abrir o dashboard:

```powershell
streamlit run dashboard/app.py --server.port 8512
```

No painel, é possível selecionar o período de análise, alternar entre as visões mensal, semanal e diária, escolher o indicador e comparar duas janelas de tempo. Os indicadores financeiros são apresentados como índices, e não em reais, para preservar informações comerciais.

## Segmentação RFM

Para a visão de clientes, apliquei a segmentação RFM:

- **Recência:** há quanto tempo a última compra foi feita;
- **Frequência:** quantidade de pedidos realizados;
- **Valor monetário:** valor histórico dos pedidos.

Os grupos encontrados são: clientes fiéis, clientes recentes, clientes em risco, baixo engajamento e oportunidade. Essa classificação ajuda a indicar possíveis ações de retenção e reativação.

## Limitações da base

- Há registros de tempo de entrega fora de uma faixa plausível. Por isso, durações menores que zero ou maiores que 180 minutos são marcadas como inconsistentes.
- A base de clientes representa um retrato histórico e não deve ser usada como correspondência perfeita para todos os pedidos do período.
- Não há dados de itens, custos ou margem. Logo, análises de rentabilidade por produto ainda não fazem parte deste case.
- Para analisar as avaliações com mais profundidade, seria necessário ter os textos em CSV/XLSX ou realizar OCR com revisão manual.

## Privacidade dos dados

Os arquivos em `dados/brutos/`, `dados/tratados/` e relatórios locais são ignorados pelo Git. Antes de publicar qualquer evolução deste projeto, reviso se não há nomes, telefones, endereços, identificadores ou valores comerciais que não deveriam ficar públicos.

## Evolução local: previsão e atualização de dados

Acrescentei uma área de previsão experimental de pedidos diários com Random Forest. Comparo o ML com a média histórica por dia da semana em três janelas cronológicas, usando MAE e RMSE. A projeção usa o método que apresentar menor MAE médio, mesmo quando a referência simples vencer o ML.

Dias sem registro não são tratados automaticamente como zero: o painel permite confirmar essa hipótese. A faixa mostrada na projeção é baseada nos erros de validação e não representa garantia de precisão. Ainda não incluo variáveis de clima, promoções e feriados.

Também incluí upload de CSV agregado, com prévia, validação e opção de adicionar/corrigir datas ou substituir a série. O arquivo precisa conter `data`, `pedidos`, `pedidos_concluidos`, `indice_faturamento` e `pontos_ticket_indice`. Datas usam `AAAA-MM-DD`; quantidades devem ser inteiras e índices devem manter a mesma referência financeira da base original. O painel fornece um modelo para download.

A atualização pode ser aplicada na sessão e salva localmente pelo botão do painel. O arquivo fica em `dados/atualizacoes/`, fora do Git, e é carregado nas próximas sessões. Ao salvar, a versão anterior é preservada em backup. Também é possível exportar a série ativa ou restaurar a base inicial na sessão. Preparo e RFM continuam referentes à exportação original, pois esses arquivos não possuem dimensão diária. Esta evolução está sendo validada localmente antes de atualizar a VPS.

Para verificar as regras de importação e previsão:

```powershell
python -m pytest testes -q
```

## Próximos passos

Pretendo evoluir o case com dados de produtos e custos para analisar margem e atualizar a implantação da VPS após a validação local.

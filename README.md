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

## Próximos passos

Pretendo evoluir o case com dados de produtos e custos para analisar margem, além de ampliar os testes das regras de tratamento e métricas.

# Previsão de demanda diária

## Objetivo e escopo

Implementei este modelo para estimar pedidos nos próximos 7 a 28 dias usando apenas atributos de calendário. Ele está em `src/previsao.py` e aparece na aba **Previsão na base pública**.

Mantenho essa abordagem separada do modelo da aba **Pedidos e faturamento**, que utiliza histórico recente e atributos agregados de clientes. Os dois modelos têm conjuntos de atributos e protocolos de avaliação diferentes; não comparo seus erros como se fossem o mesmo experimento.

## Dados e unidade de análise

Cada linha da série representa um dia observado e sua quantidade de pedidos. A base publicada até 30/09/2026 contém 194 dias com registros em um intervalo de 273 dias, iniciado em 01/01/2026.

Não transformo automaticamente os 79 dias ausentes em zero. No painel, deixo essa hipótese como uma opção explícita. Sem um calendário de abertura, interpreto a projeção como demanda em dias com operação, sem estimar a probabilidade de a loja abrir.

Começo a projeção no dia seguinte à última data da série ativa. Se o histórico estiver desatualizado, a previsão também terá uma origem antiga.

## Modelo e referência

Configurei um Random Forest Regressor com 150 árvores, mínimo de 5 observações por folha e semente 42. Uso dia da semana, mês, dia do mês, tempo decorrido desde o início da série e representação cíclica semanal.

Neste modelo, não utilizo médias de pedidos, valores defasados nem atributos de clientes. Comparei-o com a média histórica de pedidos por dia da semana. Quando um dia da semana não aparece no treino, utilizo a média geral desse treino.

## Validação

Organizei três janelas consecutivas com treinamento expansivo. Cada teste contém até 28 observações; o tamanho é definido pela quantidade de registros da série, sem acompanhar necessariamente o horizonte escolhido para a projeção.

Em cada rodada, ajusto os dois métodos somente com dados anteriores à janela avaliada. Calculo MAE e RMSE em pedidos por dia e seleciono o método com menor MAE médio. Depois, ajusto o modelo com toda a série para projetar datas futuras.

Essas janelas servem à comparação e à seleção. Não apresento os erros como resultado de um teste final independente.

Na primeira avaliação, feita com a base até 27/09/2026 e sem preencher dias ausentes, registrei:

| Método | MAE em pedidos/dia | RMSE em pedidos/dia |
|---|---:|---:|
| Random Forest | 5,09 | 6,41 |
| Média por dia da semana | 5,39 | 6,96 |

Esses resultados são um registro do experimento inicial, não as métricas da base atualizada. O painel recalcula a avaliação com a série ativa.

## Faixa de erro e limitações

Construo a faixa com o percentil 90 dos erros absolutos do método escolhido nas janelas de validação, limitando a previsão inferior a zero. Não se trata de um intervalo probabilístico calibrado nem de uma garantia de cobertura futura.

Não incluo clima, feriados, campanhas, capacidade, estoque ou calendário de abertura. Também considero a limitação do Random Forest para extrapolar tendências. Não interpreto a importância das variáveis como evidência de causalidade.

Para ampliar o uso operacional, pretendo acrescentar novas fontes e separar um período final de avaliação.

## Atualização da série

Valido os CSVs agregados antes de aplicar uma atualização. Rejeito datas duplicadas dentro do arquivo, quantidades inválidas e índices financeiros não finitos ou negativos. A quantidade de pedidos concluídos não pode exceder o total de pedidos.

No modo de adicionar ou corrigir datas, substituo a linha existente da mesma data. Para preservar a coerência entre arquivos, mantenho a referência usada nos índices financeiros.

Na versão local, posso salvar a série em `dados/atualizacoes/serie_diaria.csv`, com backup da versão anterior. Na versão pública, o upload vale somente para a sessão e não permite salvar no servidor.

O upload de CSV altera a análise temporal e o treino desse modelo. Não recalcula preparo ou RFM a partir da série diária. Para importar a exportação bruta de pedidos, uso o Excel no dashboard local ou `atualizar_pedidos.py`.

**Autor:** [Pedro Merli](https://github.com/pedrokamerli).

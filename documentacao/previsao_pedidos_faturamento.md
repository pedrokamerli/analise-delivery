# Previsão diária com histórico de clientes e pedidos

## Objetivo e implementação

Desenvolvi esta abordagem para estimar pedidos e faturamento usando calendário, demanda recente e comportamento agregado dos clientes. A implementação está em `src/historico_clientes.py` e `src/previsao_negocio.py`, na aba **Pedidos e faturamento** do dashboard.

Na aplicação local, trabalho com faturamento em reais. Na demonstração pública, uso `dados/publicos/historico_previsao.csv`, com faturamento e ticket histórico indexados.

## Fontes e proteção dos dados

Normalizo os telefones das planilhas de clientes e pedidos em memória para reconstruir o comportamento e verificar a cobertura do cadastro. Não salvo nomes, telefones, IDs de cliente ou chaves pseudonimizadas na série diária final.

Mantenho a série financeira local em `dados/tratados/historico_diario.csv`, fora do Git e da imagem Docker. Na exportação pública, indexo o faturamento para que a soma do primeiro mês com receita positiva seja 100. Também indexo o ticket histórico, sem publicar as referências monetárias usadas na conversão.

Não uso os totais atuais de PEDIDOS, FATURADO ou DIAS SEM COMPRAR do cadastro como atributos de datas anteriores. Como esses campos não têm versões históricas, reconstruo o comportamento a partir dos pedidos anteriores a cada data. A recorrência fica limitada ao período disponível.

## Definição dos alvos

- **Pedidos:** todos os pedidos registrados no dia.
- **Faturamento:** soma de TOTAL dos pedidos com status Entregue, Retirado ou Avaliado na exportação, agrupados pela data do pedido.

Não interpreto esse faturamento como lucro, margem ou fluxo de caixa. Os status representam o momento da exportação; sem uma trilha de alterações, não consigo reconstruir integralmente o que era conhecido em cada data passada.

Pedidos recentes ainda em andamento podem subestimar a receita. Essa limitação afeta tanto a análise quanto os valores usados na avaliação retrospectiva.

## Atributos utilizados

Uso calendário, tendência, último valor observado e médias de 7 e 28 dias do alvo. As médias consideram dias corridos e somente observações anteriores à data, com contagem de registros em cada janela.

Nos 28 dias anteriores, reconstruo quatro atributos agregados de clientes:

- Quantidade de clientes distintos com pedidos.
- Quantidade de clientes que fizeram mais de um pedido na janela.
- Frequência média de pedidos por cliente identificado.
- Ticket médio dos pedidos concluídos.

Esses atributos descrevem o histórico disponível; não são previsões individuais de compra nem demonstram, isoladamente, ganho no modelo.

## Validação e seleção

Comparo Random Forest e média por dia da semana separadamente para pedidos e faturamento. Configurei o Random Forest com 150 árvores, mínimo de 5 observações por folha e semente 42.

Uso três janelas cronológicas com o mesmo horizonte em dias corridos escolhido para a previsão, de 7 a 28 dias. Em cada rodada, treino apenas com dados anteriores à origem da janela.

Na projeção, congelo o contexto dos clientes no último retrato histórico do treino. Avanço as médias e o último valor recursivamente com estimativas, sem consultar os valores reais da janela futura. Sem confirmar dias ausentes como zero, avalio somente os dias registrados.

Escolho o método com menor MAE médio por alvo e também apresento RMSE. Os erros são expressos em pedidos/dia e, conforme a versão, em reais/dia ou pontos de índice/dia.

Na base até 30/09/2026, com horizonte de 14 dias e sem preencher dias ausentes, obtive:

| Alvo | Método | MAE | RMSE |
|---|---|---:|---:|
| Pedidos | Média por dia da semana | 5,64 | 6,82 |
| Pedidos | Random Forest com histórico | 4,69 | 5,62 |
| Faturamento em índice | Média por dia da semana | 3,34 | 3,82 |
| Faturamento em índice | Random Forest com histórico | 3,22 | 3,72 |

Nessa configuração, selecionei o Random Forest para os dois alvos. Reavalio a escolha quando a base ou os parâmetros mudam. Uso as mesmas janelas para comparar e selecionar; ainda não tenho um teste final independente. Não interpreto a importância das variáveis como causalidade.

## Faixas da previsão

Uso o percentil 90 dos erros absolutos de validação do método escolhido, com limite inferior zero. Essas faixas são referências empíricas por dia, sem garantia de cobertura.

Não somo os limites diários para apresentar um intervalo do total: isso exigiria considerar a dependência entre os erros de cada dia.

## Atualização do histórico

Reconstruo o histórico pelas planilhas locais, pelo fluxo `python main.py` ou pela importação de Excel em `atualizar_pedidos.py`. Ao importar pedidos, combino os registros pelo ID e recalculo os atributos históricos, preservando os meses anteriores.

Também aceito CSV agregado local com `data`, `pedidos` e `faturamento`. Os atributos de clientes são opcionais: sem eles, o modelo usa apenas o histórico de demanda e receita.

Rejeito datas duplicadas, valores negativos ou não finitos, pedidos fracionários e colunas inesperadas. Para adicionar datas ao histórico existente, exijo o mesmo esquema. Substituo datas coincidentes sem dupla contagem. Uma correção antiga exige reconstruir os atributos dos dias seguintes.

Na VPS, ativo `DELIVERY_PUBLICO=1`. Mantenho a importação de valores em reais e o salvamento no servidor bloqueados. O upload público de demonstração aceita agregações sem dados pessoais e vale apenas para a sessão; a atualização permanente depende da publicação dos arquivos públicos.

## Limites de interpretação

Começo a projeção após a última data disponível, e não automaticamente após hoje. Sem um calendário confiável de abertura, interpreto os dias projetados como demanda em dias de operação.

Ainda não incluo promoções, clima, feriados ou mudanças de capacidade. Pretendo ampliar as fontes e reservar um período independente de avaliação antes de atribuir maior confiança operacional às previsões.

**Autor:** [Pedro Merli](https://github.com/pedrokamerli).

# Case: análise e previsão de demanda de delivery

## Ponto de partida

Desenvolvi este projeto a partir das exportações de pedidos e clientes de uma operação de delivery. Meu objetivo foi organizar esse histórico para entender a demanda, acompanhar a operação e construir previsões que pudessem apoiar o planejamento dos próximos dias.

A base atual reúne **3.878 pedidos entre 01/01/2026 e 30/09/2026**. Trabalhei com informações reais, mas mantive as planilhas e os dados pessoais fora do repositório. Na demonstração pública, apresento valores financeiros em índices.

A pergunta que orientou o case foi: **como usar o histórico de pedidos para planejar a operação e identificar oportunidades de relacionamento com os clientes?**

## Como organizei o trabalho

Usei o CRISP-DM como referência. Primeiro defini as perguntas de negócio; depois examinei as exportações, tratei os campos, construí os indicadores e avaliei os métodos de previsão. Por fim, reuni os resultados em um dashboard publicado.

Não comecei pelo modelo. Antes, precisei definir o que contaria como pedido concluído, qual data usaria para agrupar o faturamento e como lidaria com dias sem registro. Essas escolhas afetam tanto os gráficos quanto a avaliação das previsões.

Considerei concluídos os pedidos com status Entregue, Retirado ou Avaliado na exportação. Agrupei o faturamento desses pedidos pela data de cadastro do pedido. Esse indicador representa receita associada a pedidos concluídos; não é lucro, margem ou fluxo de caixa.

## O que encontrei nos dados

### Concentração da demanda

No histórico disponível, **sexta, sábado e domingo somam 2.896 pedidos**, aproximadamente **74,7% do total**. Sábado concentra o maior volume, com 1.102 pedidos. Entre 19h e 20h, foram registrados 2.476 pedidos, cerca de 63,8% da base.

Essas concentrações indicam horários e dias que merecem atenção no planejamento da equipe. Não interpreto o total por dia da semana como uma comparação de produtividade: a quantidade de dias observados e o calendário de abertura podem ser diferentes. Por isso, também incluí médias por dia observado no diagnóstico.

Maio apresentou o maior volume mensal, com 564 pedidos. Ao comparar meses ou semanas, considero a cobertura de cada intervalo para evitar atribuir a uma mudança de demanda o que pode ser apenas um período parcial.

### Pedidos registrados e pedidos concluídos

A taxa de conclusão da base é de **91,4%**, conforme os status disponíveis. Mantive separados o volume registrado e o concluído para não confundir pedidos abertos, cancelados ou rejeitados com faturamento realizado.

Também deixei explícita uma limitação: os status são um retrato da exportação. Não tenho uma trilha completa de mudanças para reconstruir o que era conhecido em cada data. Isso exige cuidado ao comparar períodos recentes e interpretar a queda de conclusão ou receita.

### Qualidade dos tempos operacionais

Identifiquei **134 registros de finalização fora da faixa de 0 a 180 minutos**. Sinalizei essas durações como inconsistentes, sem tratar esse corte como um SLA da operação.

Mantive a análise de preparo com mediana e percentil 90 para observar tanto o comportamento habitual quanto tempos mais longos. Antes de recomendar uma meta de entrega, considero necessário revisar a captura dos eventos e separar erros de registro de atrasos reais.

### Recorrência de clientes

Usei a segmentação RFM para organizar o cadastro por recência, frequência e valor histórico das compras. Os grupos ajudam a levantar hipóteses de retenção e reativação, mas não demonstram que uma campanha terá retorno.

O cadastro é um retrato separado dos pedidos. Por isso, não apresento a segmentação como se ela fosse recalculada para cada filtro do dashboard. Para as previsões, reconstruí atributos agregados usando apenas pedidos anteriores a cada data, sem projetar os totais atuais do cadastro para o passado.

## Como construí as previsões

Comparei Random Forest e média histórica por dia da semana para dois alvos: pedidos e faturamento. Usei calendário, médias recentes e último valor observado, além de atributos agregados de clientes dos 28 dias anteriores.

Avaliei os métodos em três janelas cronológicas. Cada rodada foi treinada com dados anteriores ao período avaliado. Na projeção, avancei as médias com estimativas e mantive o contexto de clientes congelado na origem, sem usar compras futuras.

Com a base até 30/09/2026, horizonte de 14 dias e sem transformar dias ausentes em zero, obtive:

| Alvo | MAE da média por dia da semana | MAE do Random Forest |
|---|---:|---:|
| Pedidos | 5,64 pedidos/dia | 4,69 pedidos/dia |
| Faturamento público | 3,34 pontos de índice/dia | 3,22 pontos de índice/dia |

Nessa configuração, o Random Forest apresentou menor erro para os dois alvos. Escolho o método por alvo, sem assumir que ele será sempre o melhor após novas atualizações.

Uso essas métricas para comparação e seleção. Ainda não reservei um período final independente para avaliar o método escolhido. As faixas dos gráficos são referências empíricas dos erros diários, não garantias de vendas ou de cobertura futura.

## Como transformei a análise em uma aplicação

Construí o dashboard com Streamlit e Plotly. Nele, reúno filtros por mês, semana e dia, comparação de períodos, indicadores operacionais, segmentação de clientes e projeções diárias.

Implementei a importação local de Excel para manter o histórico atualizado. Combino os pedidos pelo ID: preservo os antigos, atualizo os repetidos e acrescento os novos. Na atualização até 30/09, incorporei 9 pedidos novos e atualizei 534 registros já existentes, sem apagar os meses anteriores.

Versionei o código no GitHub e publiquei a aplicação em uma VPS com Docker e Nginx. Reaproveitei a imagem-base de outra aplicação do servidor para reduzir o uso de disco. Essa escolha atende à implantação atual, mas cria uma dependência que documento para quem quiser reproduzir o build.

## Decisões que a análise pode apoiar

A partir dos resultados, considero úteis as seguintes ações para avaliação pela operação:

- Conferir capacidade e escala nos dias e horários de maior concentração de pedidos.
- Acompanhar conclusão e preparo junto com o volume, especialmente em períodos recentes.
- Revisar os registros de finalização antes de estabelecer metas de entrega.
- Testar ações de retenção e reativação por segmento, medindo resultados antes de ampliar campanhas.
- Atualizar o histórico antes de usar a previsão no planejamento.

Essas são recomendações derivadas da análise. Não executei intervenções para comprovar redução de atrasos, aumento de recorrência ou ganho financeiro.

## Limites e aprendizados

A base tem 194 dias observados em um intervalo de 273 dias. Não tratei automaticamente os 79 dias sem registro como zero pedidos, porque não tenho um calendário confiável de abertura.

Também não disponho de itens, custos, margem, clima ou histórico de campanhas. O PDF de avaliações não forneceu texto estruturado suficiente para uma análise de sentimentos confiável.

O principal aprendizado foi que uma previsão útil depende das definições e da qualidade dos dados que vêm antes do modelo. Neste projeto, trabalhei tanto na análise e na avaliação quanto na atualização do histórico, na proteção dos dados e na entrega da aplicação.

Como próximos passos, pretendo incorporar novas fontes, reservar um período independente de avaliação e medir o efeito das ações sugeridas. O resultado atual é uma ferramenta de exploração e apoio ao planejamento, com hipóteses e limites documentados.

## Acesso ao projeto

- [Dashboard público](https://analise-delivery.pedromerli.com/)
- [Repositório e instruções de execução](https://github.com/pedrokamerli/analise-delivery)
- [Detalhes da previsão com histórico de clientes](previsao_pedidos_faturamento.md)

**Autor:** [Pedro Merli](https://github.com/pedrokamerli).

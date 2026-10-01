# Previsão de demanda diária

## Objetivo

Estimar o número de pedidos nos próximos 7 a 28 dias para apoiar planejamento de capacidade. A previsão é experimental e não representa promessa de vendas.

## Dados e unidade de análise

Cada linha representa um dia observado, com o total de pedidos. Na base original há 193 dias registrados entre 01/01/2026 e 27/09/2026, em um calendário de 270 dias. Os 77 dias ausentes não são convertidos automaticamente em zero. O usuário pode confirmar explicitamente essa hipótese antes do treino.

Quando os dias ausentes são mantidos fora do treino, a projeção estima a demanda de um dia registrado, não a probabilidade de abertura. O horizonte começa depois da última data da série ativa; a base original já está defasada em relação à data atual.

## Modelo e referência

Random Forest com 150 árvores, mínimo de 5 observações por folha e semente 42. Atributos: dia da semana, mês, dia do mês, dias decorridos desde o início e representação cíclica semanal. Não há atributos derivados de valores futuros do alvo.

A referência é a média histórica de pedidos por dia da semana. Quando um dia da semana não existe no treino, usa-se a média geral desse treino.

## Validação

Três janelas em sequência, com treino expansivo e até 28 observações por teste. Os cortes preservam a ordem cronológica: a última data de treino sempre antecede a primeira de teste. Cada rodada ajusta ambos os métodos somente no passado.

MAE e RMSE são calculados em pedidos/dia. O método com menor MAE médio é selecionado e ajustado novamente com toda a série. As três janelas são usadas na seleção; esses erros não constituem uma avaliação final independente após selecionar o vencedor.

Na primeira avaliação local, sem preencher dias ausentes:

| Método | MAE | RMSE |
| --- | ---: | ---: |
| Random Forest | 5,09 | 6,41 |
| Média por dia da semana | 5,39 | 6,96 |

A melhora de aproximadamente 5,6% no MAE é modesta. Os resultados mudam quando a base é atualizada ou a hipótese sobre dias ausentes é alterada.

## Faixa de erro e limitações

A faixa exibida aplica o percentil 90 dos erros absolutos do método escolhido nas janelas de validação, com limite inferior truncado em zero. Ela não é um intervalo probabilístico calibrado e não garante cobertura no futuro.

Não há clima, feriados, campanhas, capacidade, estoque ou calendário de abertura. Random Forest tem limitações para extrapolar tendências. Importância das variáveis não demonstra causalidade. Uma base maior e um teste final independente devem preceder uso operacional mais exigente.

## Atualização

O painel aceita apenas agregações diárias validadas. Datas repetidas no CSV são rejeitadas; no modo de atualização, uma nova linha substitui a linha existente da mesma data. Quantidades inteiras, índices finitos não negativos e conclusão menor ou igual ao total são obrigatórios.

É possível salvar a série em `dados/atualizacoes/serie_diaria.csv`, ignorada pelo Git. O salvamento valida a base, cria backup da versão anterior e substitui o arquivo atomicamente. Os índices financeiros precisam manter a mesma referência em arquivos sucessivos.

O upload atualiza a análise temporal e o treino. Preparo e RFM permanecem um retrato histórico, pois não podem ser recalculados a partir dessas agregações diárias.

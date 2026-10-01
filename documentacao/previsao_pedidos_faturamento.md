# Previsão diária baseada em pedidos e histórico de clientes

A implementação está em `src/historico_clientes.py` e `src/previsao_negocio.py`. A aba **Pedidos e faturamento** do dashboard é a visão local em reais.

## Fontes e privacidade

Relaciono os telefones normalizados das planilhas de clientes e pedidos em memória. O cadastro permite verificar a cobertura do vínculo. Não salvo telefones, nomes, IDs de cliente ou chaves pseudonimizadas na série final. A série financeira fica em `dados/tratados/historico_diario.csv`, ignorada pelo Git e excluída do contexto Docker.

O retrato atual de PEDIDOS, FATURADO e DIAS SEM COMPRAR no cadastro não é usado como atributo de datas anteriores. Essas informações não têm versões históricas. Reconstruo o comportamento a partir dos pedidos com datas anteriores ao dia previsto. A recorrência, portanto, está limitada ao início da exportação disponível.

## Alvos

- Pedidos: todos os pedidos registrados no dia.
- Faturamento: soma de TOTAL de pedidos classificados como Entregue, Retirado ou Avaliado na exportação, agrupados pela data do pedido.

Esse faturamento não é lucro, margem ou fluxo de caixa. Os status são um retrato da exportação: não há uma trilha completa que permita saber o status de cada pedido como era conhecido em cada data passada. Pedidos recentes em andamento podem subestimar receita, e essa limitação também afeta os rótulos da avaliação retrospectiva.

## Atributos

Calendário, tendência, último valor e médias de 7 e 28 dias do alvo. As médias usam dias corridos e consideram somente observações anteriores ao dia, com contagem de observações em cada janela.

Atributos de clientes reconstruídos nos 28 dias anteriores: clientes distintos com pedidos, clientes que repetiram pedidos, frequência média de pedidos e ticket médio dos pedidos concluídos. São medidas agregadas, não previsões individuais de clientes.

## Validação e previsão futura

Comparo Random Forest com 150 árvores, mínimo de 5 observações por folha e semente 42 com a média histórica por dia da semana, separadamente para cada alvo. Uso três janelas cronológicas com o mesmo horizonte em dias corridos escolhido para a previsão, de 7 a 28 dias.

Na previsão de cada janela, o modelo é ajustado somente nos dados anteriores à sua origem. Os atributos de clientes ficam congelados no último retrato histórico disponível no treino. Médias e último valor avançam recursivamente com estimativas do modelo, sem usar os valores reais da janela de teste. Sem confirmação de dias ausentes como zero, avalio apenas os dias efetivamente registrados.

Escolho o método de menor MAE médio por alvo. Os erros servem à comparação e seleção; não são um teste final independente. MAE e RMSE de pedidos são expressos em pedidos/dia e os de faturamento em reais/dia. A importância das variáveis não demonstra que elas causaram mudanças na demanda, nem que acrescentaram ganho isoladamente.

As faixas são baseadas no percentil 90 dos erros absolutos de validação, com limite inferior zero. São referências empíricas individuais, não garantias de cobertura. Somar os limites diários não produz um intervalo confiável para o faturamento total.

## Atualização e limites

A reconstrução usa as duas planilhas locais e também é executada por `python main.py`. É possível importar CSV agregado com `data`, `pedidos` e `faturamento`; atributos de clientes são opcionais. Arquivos sem esses atributos dão origem a um modelo de histórico de demanda e receita, sem contexto de clientes.

Datas duplicadas, valores não finitos, negativos, quantidades fracionárias de pedidos e colunas inesperadas são rejeitados. Para adicionar datas a uma série existente, o esquema precisa ser idêntico. Datas coincidentes são substituídas, sem dupla contagem. Atualizações de pedidos antigos exigem reconstruir os atributos de clientes dos dias seguintes.

A projeção começa após a última data disponível, e não automaticamente após hoje. Sem um cadastro confiável de abertura da loja, dias projetados devem ser lidos como demanda condicionada a um dia de operação. Promoções, clima, feriados e mudanças de capacidade continuam fora do modelo.

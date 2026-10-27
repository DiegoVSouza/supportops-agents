# Fronteira contabilizada do Core

O caminho antigo chamava o SDK diretamente e podia alternar chaves após falha transitória. Na autorização atual, as quatro chaves compartilham a mesma conta e uma tentativa incerta não pode ser repetida. O caminho legado passa a falhar antes de ler credenciais, preservando a evidência histórica.

O novo adaptador usa o loop real do Core: classifier, knowledge worker, billing worker e responder. Cada chamada recebe uma identidade estável de campanha, caso, trial e índice. Uma falha, negativa do guard, JSON inválido ou interrupção encerra o workflow; o índice iniciado não é reutilizado. Uso desconhecido continua reservado no transporte/ledger e nunca vira zero por ausência de resposta.

O limite local reproduz a serialização completa do transporte, incluindo normalização e framing. Estado grande é rejeitado sem truncamento silencioso. O prompt recebe apenas estado real e contratos globais; expected, rubric e required facts do grader não entram nele. A paridade foi executada offline no encoder real da fronteira compartilhada.

O manifesto de execução continua desabilitado. Ainda faltam o dispatcher durável completo, congelamento do candidato, campanha alocada, revisão e qualidade live. Os workers atuais não executam ferramentas externas nem reembolsos reais; testes com contextos sintéticos não demonstram retrieval ou efeitos de produto.

## Entrevista — português

**Como impedir a repetição de uma chamada incerta?** Reservo antes do dispatch, uso uma identidade estável por tentativa e preservo a reserva quando o resultado é desconhecido. O workflow para após falha ou interrupção; um processo novo consulta recibos persistidos e não repete o mesmo índice para buscar aprovação.

## Interview — English

**How do you prevent replaying an uncertain provider operation?** Reserve before dispatch, use a stable identity for each attempt, and keep the full reservation when usage is unknown. Stop the workflow after failure or interruption. A new process checks durable receipts and cannot replay the same call index to obtain a passing result.

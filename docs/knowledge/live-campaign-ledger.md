# Ledger local para campanhas — P01

## Aprendizado

Uma campanha precisa reservar chamadas e limites antes do despacho. Se o processo cair depois de enviar a requisição e antes de salvar a resposta, o uso fica incerto: mantenha a reserva e impeça a repetição automática daquele caso/trial. Ao registrar uso desconhecido como resultado concluído, copie a reserva original para o evento novo; caso contrário, o evento mais recente pode reduzir falsamente o consumo acumulado a zero.

O ledger SQLite é local ao P01, append-only e serializa reservas concorrentes com `BEGIN IMMEDIATE`. O lease do sistema operacional evita duas campanhas locais simultâneas e não depende de metadados de segredo. A inspeção `--resume ... --dry-run` é somente leitura; ela não tenta repetir chamadas incertas.

## Limites atuais

Esta fase não implementa despacho Groq, reconciliação de faturamento do provedor, recuperação automática após crash, integração do lease a uma campanha live autorizada, nem contabilização comum aos seis projetos. O dry-run não lê credenciais e a geração continua bloqueada. Quota, limites acumulados e revisão independente continuam `PENDING`; portanto, promoção live está `INCOMPLETE`.

## Resposta de entrevista (PT-BR)

Implementei reservas duráveis antes do despacho e mantive chamadas de uso desconhecido contabilizadas. Uma falha encontrada nos testes mostrou que registrar um resultado sem tokens podia sobrescrever a reserva e subestimar consumo; corrigi a causa e provei o comportamento com teste. Ainda não afirmo que a campanha pode rodar: faltam aprovações, limites finitos e o dispatcher.

## Interview answer (English)

I added durable pre-dispatch reservations and kept unknown usage charged against the local campaign ceiling. A regression exposed that a completed result with missing token data could replace its reservation and undercount usage; I fixed the accounting and tested the failure. The campaign is still not ready to run because approvals, finite limits, and the provider dispatcher remain outstanding.

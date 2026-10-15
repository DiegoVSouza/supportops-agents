# Orquestração multiagente — conhecimento do P01

## Padrões

- **Supervisor-worker:** um supervisor escolhe o próximo worker e mantém o contrato de parada. É útil quando existe uma sequência de decisões com uma política central de encerramento. O núcleo deste projeto demonstra esse padrão.
- **Handoff:** um worker transfere o controle para outro agente ou para um humano. Registre o destino, o motivo e os dados mínimos necessários no estado compartilhado.
- **Planner-executor:** um componente formula etapas e outro executa. O plano precisa de limite e validação; caso contrário, o planejador pode aumentar o trabalho sem critério de fim.
- **Paralelismo:** tarefas independentes, como consulta à base de conhecimento e conferência de cobrança, podem rodar em paralelo. Só una resultados quando ambos terminarem, e trate falhas parciais.
- **HITL:** uma ação que exige autoridade humana pausa a execução, persiste o estado e retoma com uma decisão validada. Uma mensagem no prompt não substitui autorização real.

## Estado e falhas típicas

O estado compartilhado guarda ticket, classificação, contexto de KB, conferência de cobrança e resposta. Registros de passos explicam a sequência. Não duplique o estado em uma segunda memória sem definir qual cópia é canônica.

Loops surgem quando nenhum critério explícito encerra a execução ou quando revisões podem se repetir sem limite. Estado inconsistente aparece quando dois ramos escrevem no mesmo campo sem política de merge. Outros casos comuns são resposta sem evidência da KB, escalonamento perdido e retry que duplica efeito externo. Os testes atuais cobrem limite, aprovação, escalonamento, saída malformada, retry transitório LangGraph e retomada do checkpoint em um segundo processo.

## Quando escolher cada framework

- **Core Python:** fluxo curto, previsível e com poucas dependências.
- **LangGraph:** grafo com ramificações, retries por nó, checkpoint e interrupções humanas; este projeto implementa e testa esses comportamentos.
- **CrewAI:** equipes de agentes orientadas a papéis e tarefas, com Flow quando se quer controle estruturado.
- **AutoGen clássico:** estudo de compatibilidade com conversas multiagente clássicas; para investimento atual, avalie Microsoft Agent Framework separadamente.
- **Semantic Kernel clássico:** compatibilidade com aplicações que usam Kernel e plugins; não confundir com o sucessor Microsoft Agent Framework.
- **LlamaIndex Workflows:** aplicações cuja orquestração acompanha ingestão, retrieval e componentes de dados. As páginas oficiais recomendam Workflows para novos fluxos, em vez de QueryPipeline.

Esses cenários são orientação de arquitetura, não resultados de benchmark deste projeto. Os cinco adapters de framework executam o golden set fake; a qualidade com modelo real não foi avaliada.

## Fontes oficiais consultadas

- LangGraph: [interrupções](https://langchain-ai.github.io/langgraph/concepts/breakpoints/) e [checkpoints](https://langchain-ai.github.io/langgraph/reference/checkpoints/).
- CrewAI: [conceitos de agentes e flows](https://docs.crewai.com/core-concepts/Agents).
- Microsoft: [Agent Framework 1.0](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/), [migração AutoGen](https://learn.microsoft.com/agent-framework/migration-guide/from-autogen), [migração Semantic Kernel](https://learn.microsoft.com/agent-framework/migration-guide/from-semantic-kernel).
- LlamaIndex: [Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/) e [QueryPipeline](https://docs.llamaindex.ai/en/stable/module_guides/querying/pipeline/).

## Resposta de entrevista

**PT:** Como evitar que um supervisor multiagente entre em loop? Cada chamada conta como passo, o limite é inteiro positivo e o fluxo termina por aprovação, escalonamento ou limite. Um teste com resposta fake que nunca aprova prova a condição de parada.

**EN:** How do you prevent a multi-agent supervisor from looping forever? Every worker call counts as a step, the limit is a positive integer, and the workflow ends on approval, escalation, or the limit. A fake response that never approves proves the stop condition.

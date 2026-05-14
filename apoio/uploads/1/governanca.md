# Governanca tecnica - Ukiceker Conecta

Versao: 1.1
Data: 2026-04-18
Status: documento normativo oficial

## 1. Finalidade

Este documento define regras gerais de governanca tecnica para o Ukiceker Conecta,
com foco em integridade operacional, previsibilidade de manutencao e rastreabilidade.

Este documento e norma-mãe do projeto: orienta, limita e valida os demais documentos tecnicos.

## 2. Escopo

Aplica-se a:

- codigo-fonte em `src/nucleo`
- scripts operacionais e instalacao
- arquivos de ambiente e configuracao
- testes tecnicos em `Apoio/fonte/testes/nucleo`
- documentacao tecnica oficial em `documentacao`

## 3. Hierarquia normativa (regra de precedencia)

Ordem de prevalencia obrigatoria:

1. `documentacao/governanca.md` (norma-mãe)
2. `documentacao/ROADMAP_TECNICO_EXECUCAO.md` (execucao tecnica)
3. `documentacao/plano_de_desenvolvimento.md` (planejamento)
4. `documentacao/RESUMO_TECNICO_INTEGRACAO.md` (guia de integracao)
5. `documentacao/diario_de_bordo.md` (registro historico)
6. `Leia-me.md` (visao institucional)

Se houver conflito entre documentos, prevalece este arquivo.

## 4. Principios obrigatorios

- Runtime-first para integracao de banco.
- Governanca por evidencias: toda mudanca estrutural deve deixar rastro documental.
- Compatibilidade controlada: evitar quebra silenciosa de fluxo legado.
- Seguranca por padrao: nenhum segredo sensivel em repositório versionado.

## 5. Regras de estrutura e nomenclatura

- Pastas e arquivos devem usar nomes estaveis e previsiveis.
- Em Python: funcoes/variaveis em snake_case, classes em PascalCase e constantes em UPPER_SNAKE_CASE.
- Evitar arquivos temporarios, scripts de correcao ad-hoc e artefatos sem dono tecnico.

## 6. Regras de protocolo e integracao

- Toda sessao deve seguir o fluxo: handshake -> identify -> import_request -> operacoes.
- `identify` deve conter, no minimo: `client_id`, `origin`, `app_version`.
- `import_request` DEVE usar apenas: `api_key + profile_name` (modo unico obrigatorio).
- Envelope JSON de mensagens deve manter contrato de versao, tipo e payload.

## 7. Regras de ambiente e fallback

- `RUNTIME_DB_ONLY=1`: exige banco resolvido em runtime, sem fallback implicito.
- `RUNTIME_DB_ONLY=0`: permite fallback `DEFAULT_DB_*`.
- O fallback default deve permanecer agnostico por plataforma suportada.
- Primeiro contato valido deve hidratar `RUNTIME_DB_*`.
- Em falha de escrita no `.env`, usar fallback em `%TEMP%` sem derrubar servico.

## 8. Plataformas de dados suportadas

- mysql
- mariadb
- postgresql
- sqlserver
- oracle
- firebird
- sqlite

## 9. Regras de seguranca

- Nao versionar segredos reais (chaves, senhas, tokens, credenciais).
- Manter `FERNET_KEY` obrigatoria para fluxos que dependem de criptografia.
- Qualquer exposicao acidental de segredo deve gerar rotacao imediata e registro no diario.

## 10. Regras de testes e qualidade

- Mudanca de integracao deve vir com validacao tecnica correspondente.
- Priorizar testes independentes de infraestrutura externa para cenario base.
- Falhas conhecidas e riscos residuais devem ser documentados.

## 11. Regras de documentacao obrigatoria

Ao alterar arquitetura, conectores, payload ou variaveis de ambiente, atualizar no mesmo PR:

- `documentacao/RESUMO_TECNICO_INTEGRACAO.md`
- `documentacao/ROADMAP_TECNICO_EXECUCAO.md`
- `documentacao/plano_de_desenvolvimento.md` (quando houver impacto de planejamento)
- `documentacao/diario_de_bordo.md` (registro de decisao e impacto)
- `.env.exemplo` (exemplos de configuracao e payload)

## 12. Barreiras obrigatorias para alteracao de governanca

Qualquer alteracao neste documento exige, obrigatoriamente:

1. PR exclusivo de governanca (sem mistura com refatoracao de codigo).
2. Justificativa tecnica objetiva no corpo do PR (problema, risco, impacto).
3. Registro no `documentacao/diario_de_bordo.md` com motivacao e efeito esperado.
4. Atualizacao sincronizada dos documentos impactados pela nova regra.
5. Aprovacao explicita do responsavel arquitetural do projeto.

Sem todos os itens acima, a alteracao e considerada invalida e deve ser revertida.

## 13. Regime de nao conformidade (barreira de desobediencia)

As condutas abaixo configuram violacao grave de governanca:

- alterar fluxo tecnico sem atualizar documentacao obrigatoria;
- remover ou enfraquecer controles normativos sem emenda formal;
- introduzir segredo real em arquivo versionado;
- ignorar regra de precedencia documental.

Tratamento obrigatorio da violacao:

1. Bloqueio da entrega ate saneamento completo.
2. Reversao do trecho nao conforme.
3. Registro do incidente no `documentacao/diario_de_bordo.md`.
4. Revalidacao tecnica antes de nova aprovacao.

## 14. Regra de integridade documental

- Este arquivo nao deve ser sobrescrito com conteudo generico.
- Alteracoes devem preservar contexto do projeto e registrar motivacao no diario de bordo.
- Mudancas de governanca sem justificativa tecnica devem ser rejeitadas em revisao.
- Qualquer tentativa de bypass deste rito e tratada como incidente critico de conformidade.

## 15. Versionamento desta governanca

Formato: `vMAJOR.MINOR.PATCH`

- MAJOR: mudanca de diretriz estrutural
- MINOR: ampliacao de regra ou novo bloco normativo
- PATCH: ajustes de redacao sem mudanca de diretriz

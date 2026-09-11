import io

from rotinas.ia import gerar_conteudo
from rotinas.genericas import extrair_json, calcular_aderencia

_PROMPT = """Você é um assistente especializado em análise de currículos profissionais brasileiros de qualquer área.
Extraia as informações do currículo abaixo e retorne APENAS um JSON válido, sem markdown, sem explicações.

Estrutura esperada:
{
  "resumo_profissional": "string ou null",
  "localizacao": "Cidade, UF ou null",
  "pretensao_salarial": 0,
  "contatos": {
    "telefone": "string ou null",
    "linkedin": "URL ou null",
    "github": "URL ou null",
    "website": "URL ou null"
  },
  "experiencias": [
    {
      "cargo": "string",
      "empresa": "string",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_fim": "YYYY-MM-DD ou null",
      "em_atual": 0,
      "descricao": "string ou null"
    }
  ],
  "formacoes": [
    {
      "instituicao": "string",
      "curso": "string",
      "nivel": "graduacao|pos_graduacao|mestrado|doutorado|tecnico|curso",
      "data_inicio": "YYYY-MM-DD ou null",
      "data_conclusao": "YYYY-MM-DD ou null",
      "em_progresso": 0
    }
  ],
  "habilidades": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|especialista",
      "categoria": "juridica|tecnica|comportamental ou null"
    }
  ],
  "idiomas": [
    {
      "nome": "string",
      "proficiencia": "basico|intermediario|avancado|fluente|nativo"
    }
  ],
  "certificacoes": [
    {
      "nome": "string",
      "emissor": "string",
      "data_emissao": "YYYY-MM-DD ou null",
      "data_expiracao": "YYYY-MM-DD ou null",
      "url": "string ou null"
    }
  ]
}

Currículo:
"""


def extrair_texto_pdf(conteudo: bytes) -> str:
    import pdfplumber
    texto = []
    with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)


def extrair_texto_docx(conteudo: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(conteudo))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


_PROMPT_CURRICULO = """Você é um especialista sênior em recrutamento brasileiro e redação estratégica de currículos, com domínio em todas as áreas de atuação profissional.
Sua missão é produzir um currículo PREMIUM, altamente personalizado para a vaga abaixo, destacando exclusivamente as competências, experiências e diferenciais que impactam diretamente essa candidatura — independente da área de formação do candidato.
Siga rigorosamente o padrão ABNT NBR 9050 adaptado ao mercado de trabalho brasileiro.

DIRETRIZ PRINCIPAL: Este não é um exercício de transcrição. Você deve ANALISAR, SELECIONAR e REFORMULAR
estrategicamente as informações REAIS do candidato, apresentando-o da forma mais competitiva possível para ESTA vaga.

REGRA INVIOLÁVEL DE VERACIDADE — acima de qualquer outra instrução deste prompt:
- PROIBIDO inventar, atribuir ou implicar qualquer responsabilidade, entrega, tarefa, nível de autoridade
  ("responsável por", "coordenou", "liderou"), autoria de documento/parecer/relatório, ou atividade que o
  candidato NÃO tenha declarado explicitamente no perfil, no currículo base ou no histórico da entrevista.
- "Reformular" significa reescrever com outras palavras o que o candidato JÁ afirmou — nunca adicionar um
  fato novo. Se ele disse "atuei com contratos administrativos", é PROIBIDO virar "responsável pela
  celebração e fiscalização de contratos" (implica posse que não foi afirmada) ou "produzi pareceres
  técnicos sobre tratados internacionais" (invenção de entregável específico que ele nunca mencionou).
- Antes de escrever qualquer frase sobre experiência, verifique: "o candidato afirmou isso, com essas
  palavras ou equivalentes, em algum trecho do conteúdo fornecido?". Se não, a frase não entra — reformule
  para algo que ele de fato disse, ou simplesmente omita.
- Palavras-chave da vaga (leis, normas, siglas técnicas) só podem aparecer associadas a uma habilidade ou
  conhecimento que o candidato realmente declarou possuir — nunca como uma atividade ou entrega que ele
  nunca afirmou ter realizado.
- PROIBIDO alterar o NOME do cargo declarado pelo candidato (ex.: "Funcionário Público", "Estagiário",
  "Auxiliar") para um título que soe mais alinhado à vaga (ex.: "Analista de Contratos"). A reformulação
  vale para a DESCRIÇÃO das atividades — o nome do cargo é fato, não estilo, e deve ser reproduzido como
  o candidato declarou, mesmo que menos glamouroso do que o cargo-alvo.
- PROIBIDO reciclar a mesma frase-padrão em experiências profissionais diferentes só porque ambas tocam
  em temas parecidos. Cada bullet de cada experiência deve refletir especificamente o que foi dito PARA
  AQUELA experiência — se duas experiências têm descrições parecidas no conteúdo original, tudo bem que
  fiquem parecidas no currículo; se uma tem detalhe e a outra não, não empreste o detalhe de uma para a
  outra.

ESTRATÉGIAS OBRIGATÓRIAS (sempre subordinadas à regra de veracidade acima):
- OBJETIVO PROFISSIONAL: 2-3 linhas que conectem diretamente a trajetória real do candidato ao cargo
  pretendido, usando palavras-chave da descrição da vaga apenas onde há correspondência real
- REFRAME DE EXPERIÊNCIAS: reescreva a DESCRIÇÃO do que o candidato já fez usando termos mais adequados
  à vaga-alvo — sem adicionar responsabilidade, tarefa ou entrega nova, e sem trocar o nome do cargo.
  Exemplo correto: candidato disse "trabalhei com gestão de equipe" → "liderança de equipes e gestão de
  processos" (mesma informação, outras palavras). Exemplo PROIBIDO: candidato nunca mencionou auditoria →
  não escrever "coordenou auditorias". Candidatos multidisciplinares têm trajetória rica — valorize cada
  área real como diferencial complementar
- SELEÇÃO INTELIGENTE DE HABILIDADES — a mais negligenciada e a mais importante contra currículo inflado:
  liste em HABILIDADES apenas o que tem relação DIRETA com o domínio da vaga. Um conhecimento de um domínio
  totalmente alheio à vaga (ex.: stack de programação — Python, frameworks, bancos de dados — numa vaga
  jurídica/administrativa que não pede nada disso) deve ser OMITIDO, mesmo que conste no perfil do
  candidato — não é mentira incluir, mas é diluição: um currículo que lista tudo o que o candidato sabe,
  sem filtro, parece inflado e enfraquece o que de fato importa para esta vaga. Regra prática: para cada
  habilidade candidata a entrar na lista, pergunte "um recrutador desta vaga específica bateria o olho
  nisso e pensaria 'relevante'?" — se não, fica de fora
- ENTREVISTA: use as informações coletadas para enriquecer com detalhes ESPECÍFICOS que o candidato de
  fato forneceu — nunca para preencher lacunas com suposições
- DOCUMENTOS COMPLEMENTARES: se houver seção "DOCUMENTO COMPLEMENTAR ANEXADO" no conteúdo do candidato,
  garimpe-a ativamente — histórico acadêmico pode conter disciplinas relevantes à vaga, um certificado pode
  justificar uma habilidade, um portfólio pode conter projetos concretos. Não basta ela existir no contexto:
  extraia o que for pertinente a ESTA vaga e incorpore nas seções apropriadas (formação, habilidades,
  certificações). Ignorar um documento anexado é desperdiçar informação real que o candidato forneceu

FORMATAÇÃO ABNT OBRIGATÓRIA — siga EXATAMENTE este modelo:

Linha 1: NOME COMPLETO EM MAIÚSCULO
Linha 2: cidade, UF | telefone | e-mail (apenas os dados disponíveis, separados por |)
Linha 3: em branco
Linha 4: NOME DA SEÇÃO (ex: OBJETIVO PROFISSIONAL)
Linha 5: texto da seção

REGRAS DE FORMATAÇÃO — cada uma é inviolável:
- Títulos de seção: apenas texto em MAIÚSCULAS, sem qualquer caractere decorativo antes ou depois
- PROIBIDO usar traços ou hifens como separadores de seção (---------------) — o título em maiúsculo já delimita
- Cargos e empresas: escreva o nome diretamente, sem nenhum asterisco
  CORRETO:   Funcionário Público – Governo da Paraíba
  ERRADO:    **Funcionário Público** – Governo da Paraíba
- Datas no formato Mês/AAAA – Mês/AAAA (ou "atual"), apenas dentro de cada item
- Bullet points com hífen (-) para responsabilidades e habilidades
- Uma linha em branco entre seções
- Linguagem objetiva, sem adjetivos vazios ("dinâmico", "proativo", "dedicado" são proibidos)
- PROIBIDO: **, *, ##, _sublinhado_, ~~tachado~~ ou qualquer outra sintaxe markdown
- PROIBIDO: CPF, RG, endereço completo, foto, idade, estado civil
- PROIBIDO: data de geração, rodapé, cabeçalho com data ou hora
- Retorne APENAS o texto puro do currículo, começando pelo nome do candidato — nada mais

ESTRUTURA DAS SEÇÕES (nesta ordem, inclua apenas as que tiverem dados):
DADOS DE CONTATO → OBJETIVO PROFISSIONAL → FORMAÇÃO ACADÊMICA → EXPERIÊNCIA PROFISSIONAL → HABILIDADES → IDIOMAS → CERTIFICAÇÕES E CURSOS

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL BASE DO CANDIDATO:
{perfil}

INFORMAÇÕES ADICIONAIS DA ENTREVISTA (use se disponíveis):
{historico}
"""

def processar_score_com_ia(titulo: str, descricao: str, perfil: str) -> dict:
    """Wrapper de compatibilidade — a régua de aderência agora é agnóstica
    e vive em rotinas/genericas.py (calcular_aderencia), reutilizada aqui
    e na entrevista (conduzir_entrevista)."""
    return calcular_aderencia(titulo, descricao, perfil)


def processar_curriculo_com_ia(texto: str) -> dict:
    return extrair_json(gerar_conteudo(_PROMPT + texto))


def gerar_curriculo_com_ia(titulo: str, descricao: str, perfil: str, historico: str = "") -> str:
    prompt = (
        _PROMPT_CURRICULO
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
        .replace("{historico}", historico or "(sem informações adicionais da entrevista)")
    )
    return gerar_conteudo(prompt)


_PROMPT_RECRUTADOR = """Você é um recrutador sênior brasileiro conduzindo uma entrevista estruturada para a vaga abaixo.
A aderência do candidato à vaga já foi calculada por outra rotina — você NÃO deve recalculá-la nem estimar um número próprio. Use o valor informado em ADERÊNCIA ATUAL apenas para decidir o andamento da conversa.

Seu objetivo é aprofundar especificamente nos requisitos que a vaga exige e que ainda não constam no perfil do candidato — orientando-o a esclarecer se possui elementos adicionais pertinentes (competências técnicas, experiências relevantes, arquivos complementares ou diferenciais competitivos). A premissa é que uma lacuna pode ser ausência de informação, não de capacidade.

INSTRUÇÕES:
- Observe PRIMEIRO a existência de contexto no histórico da conversa: caso não exista, apresente-se apenas como "Recrutador SAR" sem inventar nome próprio ou empresa, e conduza a entrevista na premissa de início de avaliação — PROIBIDO referenciar conversas, trocas ou informações que não constem explicitamente no histórico, nunca use expressões como "conforme conversamos" ou "como discutimos"
- Faça APENAS UMA pergunta por vez — seja objetivo, profissional e cordial
- Foque nas lacunas entre o perfil do candidato e os requisitos da vaga
- Leve em conta tudo que o candidato já respondeu no histórico da conversa
- Se ADERÊNCIA ATUAL for 75 ou mais, informe o candidato que atingiu a aderência mínima e pergunte sutilmente se deseja acrescentar alguma informação relevante antes de encerrar; se ele não acrescentar nada novo, encerre cordialmente sem fazer mais perguntas
- Em momento oportuno da entrevista (após cobrir experiência e formação, antes de encerrar),
  pergunte ao candidato se ele possui documentos complementares que gostaria de compartilhar —
  como certificados, declarações, portfólio ou comprovantes de cursos. Deixe claro que é opcional
  e que ele pode enviá-los pelo botão de anexo (📎) disponível na tela

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL ATUAL DO CANDIDATO:
{perfil}

ADERÊNCIA ATUAL (0-100, já calculada — não recalcule): {aderencia}

HISTÓRICO DA CONVERSA:
{historico}

Retorne APENAS um JSON válido, sem markdown, sem explicações:
{
  "mensagem": "sua mensagem para o candidato"
}
"""


_PROMPT_CARTA = """Você é um especialista sênior em recrutamento brasileiro e comunicação profissional.
Redija uma carta de apresentação PREMIUM, personalizada para a vaga abaixo, com base no perfil e no histórico da entrevista do candidato.

REGRAS INVIOLÁVEIS:
- Extensão: 3 parágrafos (abertura, corpo, fechamento) — máximo 250 palavras
- Tom: profissional, direto, sem adjetivos vazios ("dinâmico", "proativo", "dedicado")
- Conecte explicitamente a trajetória do candidato aos requisitos da vaga
- Primeiro parágrafo: apresentação e intenção (mencione o cargo pelo nome)
- Segundo parágrafo: 2-3 diferenciais concretos do candidato para esta vaga
- Terceiro parágrafo: chamada para ação (disponibilidade para entrevista)
- PROIBIDO: markdown, asteriscos, títulos em maiúsculo, bullet points, data, rodapé
- PROIBIDO: CPF, RG, endereço, idade, estado civil
- Retorne APENAS o texto puro da carta, começando pela saudação — nada mais

VAGA:
Título: {titulo}
Descrição: {descricao}

PERFIL DO CANDIDATO:
{perfil}

INFORMAÇÕES ADICIONAIS DA ENTREVISTA:
{historico}
"""


def gerar_carta_com_ia(titulo: str, descricao: str, perfil: str, historico: str = "") -> str:
    prompt = (
        _PROMPT_CARTA
        .replace("{titulo}", titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}", perfil)
        .replace("{historico}", historico or "(sem informações adicionais da entrevista)")
    )
    return gerar_conteudo(prompt)


_PROMPT_ENRIQUECIMENTO = """Você é um extrator de dados estruturados de entrevistas profissionais.
Analise APENAS o histórico da conversa abaixo e extraia as habilidades e experiências profissionais que o candidato DECLAROU EXPLICITAMENTE durante a entrevista — não o que já estava no perfil base.

Retorne APENAS um JSON válido, sem markdown, sem explicações:
{
  "habilidades": [
    {"nome": "string", "proficiencia": "basico|intermediario|avancado|especialista", "categoria": "juridica|tecnica|comportamental"}
  ],
  "experiencias": [
    {"cargo": "string", "empresa": "string", "descricao": "string ou null"}
  ]
}

Se nada novo foi atestado em alguma categoria, retorne lista vazia para ela.

HISTÓRICO DA ENTREVISTA:
{historico}
"""


def extrair_enriquecimento_entrevista(historico: list) -> dict:
    hist_texto = "\n".join(
        f"{h['role'].upper()}: {h['conteudo']}" for h in historico
    )
    prompt = _PROMPT_ENRIQUECIMENTO.replace("{historico}", hist_texto)
    try:
        resultado = extrair_json(gerar_conteudo(prompt))
        return {
            "habilidades": resultado.get("habilidades") or [],
            "experiencias": resultado.get("experiencias") or [],
        }
    except Exception as e:
        print(f"[ERRO extrair_enriquecimento_entrevista] {type(e).__name__}: {e}")
        return {"habilidades": [], "experiencias": []}


def conduzir_entrevista(titulo: str, descricao: str, perfil: str, historico: list, score_anterior: float = 0) -> dict:
    hist_texto = "\n".join(
        f"{h['role'].upper()}: {h['conteudo']}" for h in historico
    ) if historico else "(nenhuma troca anterior — inicie a entrevista apresentando-se)"

    # Aderência calculada pela régua única e agnóstica (rotinas/genericas.py) —
    # a mesma usada em "Ver aderência" na lista de vagas. Nunca regride abaixo
    # de score_anterior, e o prompt do recrutador não tem permissão de recalculá-la.
    try:
        aderencia = calcular_aderencia(titulo, descricao, perfil, historico=hist_texto, score_anterior=score_anterior)
        score = aderencia.get("score", score_anterior)
    except Exception as e:
        print(f"[ERRO calcular_aderencia] {type(e).__name__}: {e}")
        score = score_anterior

    prompt = (
        _PROMPT_RECRUTADOR
        .replace("{titulo}",   titulo)
        .replace("{descricao}", descricao or "Não informada")
        .replace("{perfil}",   perfil)
        .replace("{aderencia}", str(int(score)))
        .replace("{historico}", hist_texto)
    )

    try:
        resultado = extrair_json(gerar_conteudo(prompt))
    except Exception as e:
        print(f"[ERRO conduzir_entrevista] {type(e).__name__}: {e}")
        resultado = {"mensagem": "Desculpe, tive um problema ao processar. Pode repetir sua resposta?"}

    resultado["score_estimado"] = score
    resultado["pronto"] = score >= 75
    return resultado

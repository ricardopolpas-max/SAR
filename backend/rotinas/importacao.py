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

DIRETRIZ PRINCIPAL: Este não é um exercício de transcrição. Você deve ANALISAR, SELECIONAR e TRANSFORMAR
estrategicamente as informações, apresentando o candidato da forma mais competitiva possível para ESTA vaga.

ESTRATÉGIAS OBRIGATÓRIAS:
- OBJETIVO PROFISSIONAL: 2-3 linhas que conectem diretamente a trajetória do candidato ao cargo pretendido,
  usando palavras-chave da descrição da vaga
- REFRAME DE EXPERIÊNCIAS: Traduza cargos anteriores em competências transferíveis para a vaga-alvo.
  Candidatos multidisciplinares têm trajetória rica — valorize cada área como diferencial complementar.
  Exemplos: gerência → liderança de equipes e gestão de processos; programação → análise de sistemas e
  automação; eletricidade → conformidade técnica e gestão de contratos de manutenção; condução de veículos
  pesados → logística, responsabilidade e cumprimento de normas regulatórias
- SELEÇÃO INTELIGENTE: Inclua apenas o que agrega valor para esta vaga — omita o que não contribui
- ENTREVISTA: Use as informações coletadas para enriquecer com detalhes específicos desta candidatura
- DOCUMENTOS: Se o candidato enviou arquivos complementares, use o conteúdo para fortalecer com evidências

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

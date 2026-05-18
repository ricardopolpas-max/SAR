/* ============================================================
   SAR — curriculos.js
   Recrutador IA — entrevista guiada para geração de currículo
   personalizado por vaga (Motor 4 Bloco 5).
   ============================================================ */

let _curriculoVagaId     = null;
let _curriculoVagaTitulo  = "";
let _curriculoVagaEmpresa = "";
let _curriculoGerado      = false; // true após geração bem-sucedida; false ao iniciar nova entrevista

const _VAZIO_HTML_ORIGINAL = document.getElementById("curriculos-vazio").innerHTML;

/* ----------------------------------------------------------
   ESTADOS — controla qual painel é exibido
---------------------------------------------------------- */
function _mostrarEstadoCurriculo(estado) {
  document.getElementById("curriculos-vazio").classList.toggle("hidden",    estado !== "vazio");
  document.getElementById("curriculos-chat").classList.toggle("hidden",     estado !== "chat");
  document.getElementById("curriculos-gerando").classList.toggle("hidden",  estado !== "gerando");
  document.getElementById("curriculos-resultado").classList.toggle("hidden", estado !== "resultado");
}

/* ----------------------------------------------------------
   SCORE — atualiza barra de aderência
---------------------------------------------------------- */
function _atualizarScore(score) {
  const pct       = Math.min(Math.max(Math.round(score), 0), 100);
  const barra     = document.getElementById("chat-barra-preenchida");
  const valor     = document.getElementById("chat-score-valor");
  const gerarArea = document.getElementById("chat-gerar-area");

  valor.textContent  = pct + "%";
  barra.style.width  = pct + "%";

  const atingido = pct >= 75;
  valor.classList.toggle("atingido", atingido);
  barra.classList.toggle("atingido", atingido);
  gerarArea.classList.toggle("hidden", !atingido);
}

/* ----------------------------------------------------------
   MENSAGENS — bolhas de chat
---------------------------------------------------------- */
function _adicionarMensagem(role, texto) {
  if (!texto || !texto.trim()) return null;

  const area  = document.getElementById("chat-mensagens");
  const wrap  = document.createElement("div");
  wrap.className = "chat-bolha " + (role === "ia" ? "chat-bolha-ia" : "chat-bolha-usuario");

  const autor = document.createElement("div");
  autor.className   = "chat-bolha-autor";
  autor.textContent = role === "ia" ? "Recrutador" : "Você";

  const bolha = document.createElement("div");
  bolha.className   = "chat-bolha-texto";
  bolha.textContent = texto;

  wrap.appendChild(autor);
  wrap.appendChild(bolha);
  area.appendChild(wrap);
  area.scrollTop = area.scrollHeight;
  return wrap;
}

function _mostrarDigitando() {
  const area = document.getElementById("chat-mensagens");
  const wrap = document.createElement("div");
  wrap.id        = "chat-digitando-bolha";
  wrap.className = "chat-bolha chat-bolha-ia chat-digitando";

  const autor = document.createElement("div");
  autor.className   = "chat-bolha-autor";
  autor.textContent = "Recrutador";

  const bolha = document.createElement("div");
  bolha.className   = "chat-bolha-texto";
  bolha.textContent = "digitando…";

  wrap.appendChild(autor);
  wrap.appendChild(bolha);
  area.appendChild(wrap);
  area.scrollTop = area.scrollHeight;
}

function _removerDigitando() {
  const el = document.getElementById("chat-digitando-bolha");
  if (el) el.remove();
}

function _renderizarHistorico(historico) {
  document.getElementById("chat-mensagens").innerHTML = "";
  if (!historico || !historico.length) return;
  historico.forEach(function (h) {
    if (h.conteudo && h.conteudo.trim()) {
      _adicionarMensagem(h.role === "candidato" ? "usuario" : "ia", h.conteudo);
    }
  });
}

/* ----------------------------------------------------------
   CHAT — inicialização
---------------------------------------------------------- */
async function _iniciarChat() {
  const checaPerfil = await SarAPI.perfil.carregar();
  if (!checaPerfil.ok || !checaPerfil.dados || !checaPerfil.dados.dados) {
    document.getElementById("curriculos-vazio").innerHTML = `
      <div class="estado-container">
        <div class="estado-icone">📋</div>
        <div class="estado-titulo">Currículo não importado</div>
        <p class="estado-descricao">
          Para iniciar a entrevista com o Recrutador IA, é necessário primeiro importar
          seu currículo em <strong>Meu Perfil</strong>.<br><br>
          A IA usará esse documento como ponto de partida para conhecer seu perfil
          e conduzir a entrevista.
        </p>
        <button class="btn btn-primario"
          onclick="document.querySelector('.nav-item[data-secao=&quot;perfil&quot;]').click()">
          Ir para Meu Perfil
        </button>
      </div>`;
    _mostrarEstadoCurriculo("vazio");
    return;
  }

  document.getElementById("curriculos-vazio").innerHTML = _VAZIO_HTML_ORIGINAL;

  document.getElementById("chat-vaga-titulo").textContent  = _curriculoVagaTitulo;
  document.getElementById("chat-vaga-empresa").textContent = _curriculoVagaEmpresa;
  document.getElementById("chat-mensagens").innerHTML      = "";
  document.getElementById("chat-input").value              = "";
  _curriculoGerado = false;
  _atualizarScore(0);
  _mostrarEstadoCurriculo("chat");

  const { ok, dados } = await SarAPI.vagas.carregarConversa(_curriculoVagaId);

  if (ok && dados && dados.historico && dados.historico.length) {
    _renderizarHistorico(dados.historico);
    _atualizarScore(dados.score_estimado || 0);
    return;
  }

  _mostrarDigitando();
  const resp = await SarAPI.vagas.conversar(_curriculoVagaId, "");
  _removerDigitando();

  if (resp.ok && resp.dados) {
    _adicionarMensagem("ia", resp.dados.resposta);
    _atualizarScore(resp.dados.score_estimado || 0);
  } else {
    _adicionarMensagem("ia", "Olá! Vou entrevistá-lo para conhecê-lo melhor e adaptar seu currículo à vaga. Pode começar se apresentando.");
  }
}

/* ----------------------------------------------------------
   CHAT — envio de mensagem
---------------------------------------------------------- */
async function _enviarMensagem() {
  const input = document.getElementById("chat-input");
  const texto = input.value.trim();
  if (!texto || !_curriculoVagaId) return;

  input.value    = "";
  input.disabled = true;
  document.getElementById("btn-chat-enviar").disabled = true;

  _adicionarMensagem("usuario", texto);
  _mostrarDigitando();

  const { ok, dados } = await SarAPI.vagas.conversar(_curriculoVagaId, texto);
  _removerDigitando();

  input.disabled = false;
  document.getElementById("btn-chat-enviar").disabled = false;
  input.focus();

  if (!ok) {
    _adicionarMensagem("ia", "Desculpe, tive um problema de conexão. Por favor, tente novamente.");
    return;
  }

  _adicionarMensagem("ia", dados.resposta);
  _atualizarScore(dados.score_estimado || 0);
}

/* ----------------------------------------------------------
   GERAÇÃO — currículo final via IA
---------------------------------------------------------- */
async function _gerarCurriculo() {
  if (!_curriculoVagaId) return;

  _mostrarEstadoCurriculo("gerando");
  document.getElementById("curriculos-gerando-titulo").textContent =
    "Gerando currículo para: " + (_curriculoVagaTitulo || "vaga selecionada") + "…";

  const { ok, dados, erro } = await SarAPI.vagas.gerarCurriculo(_curriculoVagaId);

  if (!ok) {
    alert("Erro ao gerar currículo:\n" + erro);
    _mostrarEstadoCurriculo("chat");
    return;
  }

  const vaga = dados.vaga || {};
  const info = vaga.titulo + (vaga.empresa ? " · " + vaga.empresa : "");
  const textoCurriculo = dados.curriculo || "";
  document.getElementById("curriculos-vaga-info").textContent  = info;
  document.getElementById("curriculos-texto").value            = textoCurriculo;
  document.getElementById("curriculos-texto-display").textContent = textoCurriculo;
  _curriculoGerado = true;
  _mostrarEstadoCurriculo("resultado");
}

/* ----------------------------------------------------------
   RESTAURAÇÃO — carrega o último currículo gerado ao entrar
   na seção sem vaga selecionada (retorno de sessão)
---------------------------------------------------------- */
async function _restaurarUltimoCurriculo() {
  const { ok, dados } = await SarAPI.perfil.listarCurriculosGerados();
  if (!ok || !dados || !dados.dados || !dados.dados.length) return false;

  const ultimo = dados.dados[0];
  if (!ultimo.conteudo) return false;

  const vaga = ultimo.vaga || {};
  _curriculoVagaId      = vaga.id    || null;
  _curriculoVagaTitulo  = vaga.titulo  || "";
  _curriculoVagaEmpresa = vaga.empresa || "";

  // Popula cabeçalho do chat e o resultado
  const info = ultimo.descricao || (vaga.titulo + (vaga.empresa ? " · " + vaga.empresa : ""));
  document.getElementById("chat-vaga-titulo").textContent           = _curriculoVagaTitulo;
  document.getElementById("chat-vaga-empresa").textContent          = _curriculoVagaEmpresa;
  document.getElementById("curriculos-vaga-info").textContent       = info;
  document.getElementById("curriculos-texto").value                 = ultimo.conteudo;
  document.getElementById("curriculos-texto-display").textContent   = ultimo.conteudo;

  // Restaura histórico do chat e score em background
  if (_curriculoVagaId) {
    const conv = await SarAPI.vagas.carregarConversa(_curriculoVagaId);
    const convDados = conv.ok && conv.dados && conv.dados.dados; // double-wrap: _requisitar envolve a resposta
    if (convDados && convDados.historico && convDados.historico.length) {
      _renderizarHistorico(convDados.historico);
      _atualizarScore(convDados.score_estimado || 0);
    }
  }
  _curriculoGerado = true;

  _mostrarEstadoCurriculo("resultado");
  return true;
}

/* ----------------------------------------------------------
   API PÚBLICA — chamada por vagas.js (navegação já feita lá)
---------------------------------------------------------- */
function iniciarGeracaoCurriculo(vagaId, vagaTitulo, vagaEmpresa) {
  _curriculoVagaId      = vagaId;
  _curriculoVagaTitulo  = vagaTitulo  || "";
  _curriculoVagaEmpresa = vagaEmpresa || "";
  _iniciarChat();
}

/* Chamada quando o usuário navega para a seção */
async function entrarSecaoCurriculos() {
  // Entrevista em andamento (sem currículo gerado ainda) — não interfere
  if (_curriculoVagaId && !_curriculoGerado) return;
  // Currículo já gerado nesta sessão — só re-exibe resultado
  if (_curriculoGerado) {
    _mostrarEstadoCurriculo("resultado");
    return;
  }
  // Primeira entrada ou nova sessão — tenta restaurar do backend
  const restaurado = await _restaurarUltimoCurriculo();
  if (!restaurado) _mostrarEstadoCurriculo("vazio");
}

/* ----------------------------------------------------------
   EVENT LISTENERS
---------------------------------------------------------- */
document.getElementById("btn-chat-enviar").addEventListener("click", _enviarMensagem);

document.getElementById("chat-input").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    _enviarMensagem();
  }
});

document.getElementById("btn-chat-reiniciar").addEventListener("click", async function () {
  if (!_curriculoVagaId) return;
  if (!confirm("Reiniciar a entrevista apagará toda a conversa atual. Confirmar?")) return;

  await SarAPI.vagas.resetarConversa(_curriculoVagaId);

  document.getElementById("chat-mensagens").innerHTML = "";
  document.getElementById("chat-gerar-area").classList.add("hidden");
  _atualizarScore(0);

  _mostrarDigitando();
  const resp = await SarAPI.vagas.conversar(_curriculoVagaId, "");
  _removerDigitando();

  if (resp.ok && resp.dados) {
    _adicionarMensagem("ia", resp.dados.resposta);
    _atualizarScore(resp.dados.score_estimado || 0);
  }
});

document.getElementById("btn-gerar-curriculo-final").addEventListener("click", _gerarCurriculo);

document.getElementById("chat-arquivo-input").addEventListener("change", async function () {
  const arquivo = this.files[0];
  if (!arquivo || !_curriculoVagaId) return;
  this.value = "";

  const descricao = arquivo.name;
  const bolhaEnviando = _adicionarMensagem("usuario", "📎 Enviando documento: " + arquivo.name + "…");

  const { ok, dados, texto_extraido } = await SarAPI.perfil.documentos.uploadComplementar(arquivo, descricao);

  if (bolhaEnviando) bolhaEnviando.remove();

  if (!ok) {
    _adicionarMensagem("ia", "Não foi possível receber o documento. Verifique o formato (PDF, DOCX ou TXT) e tente novamente.");
    return;
  }

  const contexto = texto_extraido
    ? "Recebi e li o documento '" + arquivo.name + "'. Conteúdo:\n" + texto_extraido.slice(0, 3000)
    : "Recebi o documento complementar: " + arquivo.name + ".";

  _adicionarMensagem("usuario", "📎 Documento enviado: " + arquivo.name);
  _mostrarDigitando();

  const resp = await SarAPI.vagas.conversar(_curriculoVagaId, contexto);
  _removerDigitando();

  if (resp.ok && resp.dados) {
    _adicionarMensagem("ia", resp.dados.resposta);
    _atualizarScore(resp.dados.score_estimado || 0);
  }
});

function _obterTextoCurriculo() {
  return document.getElementById("curriculos-texto-display").innerText || "";
}

document.getElementById("btn-curriculo-copiar").addEventListener("click", function () {
  const texto = _obterTextoCurriculo();
  if (!texto) return;
  navigator.clipboard.writeText(texto).then(() => {
    this.textContent = "Copiado ✓";
    setTimeout(() => { this.textContent = "Copiar texto"; }, 2000);
  }).catch(function () {
    alert("Não foi possível copiar automaticamente. Selecione o texto manualmente.");
  });
});

document.getElementById("btn-curriculo-pdf").addEventListener("click", function () {
  const texto = _obterTextoCurriculo();
  if (!texto) return;

  const titulo = _curriculoVagaTitulo ? "Currículo — " + _curriculoVagaTitulo : "Currículo";

  const linhas = texto.split("\n").map(function (linha) {
    const esc = linha.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const trimmed = linha.trim();
    if (trimmed === "") return "<br>";
    // Linha toda em maiúsculo com ao menos 3 chars = título de seção ABNT
    if (trimmed === trimmed.toUpperCase() && trimmed.length > 2 && /[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ]/.test(trimmed)) {
      return "<h2>" + esc + "</h2>";
    }
    return "<p>" + esc + "</p>";
  }).join("");

  const janela = window.open("", "_blank");
  janela.document.write(
    "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'>" +
    "<title>" + titulo + "</title>" +
    "<style>" +
    "@page{size:A4;margin:2cm;}" +
    "html,body{margin:0;padding:0}" +
    "body{font-family:'Times New Roman',Georgia,serif;font-size:12pt;line-height:1.6;color:#111;" +
    "padding:2cm;text-align:justify}" +
    "h2{font-size:11pt;font-weight:bold;text-transform:uppercase;letter-spacing:0.5px;" +
    "border-bottom:1px solid #333;margin-top:1.4em;margin-bottom:0.5em;padding-bottom:2px;" +
    "text-align:left}" +
    "p{margin:0.15em 0;text-align:justify}" +
    "br{display:block;margin:0.5em 0}" +
    ".aviso-impressao{background:#fef9c3;border:1px solid #fde047;border-radius:6px;" +
    "padding:10px 16px;margin-bottom:20px;font-family:Arial,sans-serif;font-size:11pt;color:#713f12;}" +
    ".aviso-impressao strong{display:block;margin-bottom:4px;}" +
    "@media print{.aviso-impressao{display:none}}" +
    "@media print{" +
    "html,body{margin:0;padding:0}" +
    "body{padding:0}" +
    "}" +
    "</style></head><body>" +
    "<div class='aviso-impressao'>" +
    "<strong>⚙️ Antes de imprimir:</strong>" +
    "No diálogo de impressão, desmarque a opção <strong>\"Cabeçalhos e rodapés\"</strong> " +
    "(ou <strong>\"Headers and footers\"</strong>) para um PDF limpo sem data e URL." +
    "</div>" +
    linhas +
    "<script>window.onload=function(){window.print()}<\/script>" +
    "</body></html>"
  );
  janela.document.close();
});

document.getElementById("btn-curriculo-regerar").addEventListener("click", _gerarCurriculo);

document.getElementById("btn-ver-entrevista").addEventListener("click", function () {
  document.getElementById("btn-chat-voltar-curriculo").classList.remove("hidden");
  _mostrarEstadoCurriculo("chat");
});

document.getElementById("btn-chat-voltar-curriculo").addEventListener("click", function () {
  _mostrarEstadoCurriculo("resultado");
});

/* ----------------------------------------------------------
   ESTADO INICIAL
---------------------------------------------------------- */
_mostrarEstadoCurriculo("vazio");

/* ============================================================
   Fim — curriculos.js
   ============================================================ */

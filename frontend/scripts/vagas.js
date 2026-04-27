/* ============================================================
   SAR — vagas.js
   Lógica da tela principal: status do backend e listagem de vagas.
   ============================================================ */

/* ----------------------------------------------------------
   ELEMENTOS DO DOM
---------------------------------------------------------- */
const el = {
  statusDot:    document.getElementById("status-dot"),
  statusTexto:  document.getElementById("status-texto"),
  listaVagas:   document.getElementById("lista-vagas"),
  estadoVazio:  document.getElementById("estado-vazio"),
  estadoErro:   document.getElementById("estado-erro"),
  estadoErroMsg:document.getElementById("estado-erro-msg"),
};

/* ----------------------------------------------------------
   STATUS DO BACKEND
---------------------------------------------------------- */
async function verificarBackend() {
  const { ok } = await SarAPI.sistema.ping();

  if (ok) {
    el.statusDot.classList.add("online");
    el.statusTexto.textContent = "backend online";
  } else {
    el.statusDot.classList.add("offline");
    el.statusTexto.textContent = "backend offline";
  }
}

/* ----------------------------------------------------------
   RENDERIZAÇÃO
---------------------------------------------------------- */
function badgeStatus(status) {
  const mapa = {
    PENDENTE:  "badge-pendente",
    APROVADA:  "badge-aprovada",
    REPROVADA: "badge-reprovada",
    "EM CURSO": "badge-em-curso",
  };
  const classe = mapa[status] || "badge-pendente";
  return `<span class="badge ${classe}">${status}</span>`;
}

function renderizarVaga(v) {
  return `
    <div class="card card-vaga">
      <span class="card-titulo vaga-titulo">${v.titulo}</span>
      <div class="vaga-badge">${badgeStatus(v.status)}</div>
      <div class="vaga-meta">
        <span class="vaga-empresa">${v.empresa || "Empresa não informada"}</span>
        ${v.score ? `<span class="score-chip">Score ${v.score.toFixed(1)}</span>` : ""}
        ${v.link  ? `<a href="${v.link}" target="_blank" rel="noopener noreferrer" class="btn btn-ghost btn-sm">Ver vaga ↗</a>` : ""}
      </div>
    </div>
  `;
}

/* ----------------------------------------------------------
   CARREGAMENTO DE VAGAS
---------------------------------------------------------- */
async function carregarVagas() {
  const { ok, dados, erro } = await SarAPI.vagas.listar();

  if (!ok) {
    el.estadoErroMsg.textContent = erro;
    el.estadoErro.classList.remove("hidden");
    el.statusDot.className = "status-dot offline";
    el.statusTexto.textContent = "backend offline";
    return;
  }

  if (!dados.length) {
    el.estadoVazio.classList.remove("hidden");
    return;
  }

  el.listaVagas.innerHTML = dados.map(renderizarVaga).join("");
}

/* ----------------------------------------------------------
   INICIALIZAÇÃO
---------------------------------------------------------- */
(async () => {
  await verificarBackend();
  await carregarVagas();
})();

/* ============================================================
   Fim — vagas.js
   ============================================================ */

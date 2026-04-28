/* ============================================================
   SAR — vagas.js
   Lógica da tela de vagas: listagem, filtros e sincronização.
   ============================================================ */

/* ----------------------------------------------------------
   ELEMENTOS DO DOM
---------------------------------------------------------- */
const el = {
  statusPonto:   document.getElementById("status-ponto"),
  statusTexto:   document.getElementById("status-texto"),
  vagasGrid:     document.getElementById("vagas-grid"),
  vagasContagem: document.getElementById("vagas-contagem"),
  btnSync:       document.getElementById("btn-sync"),
  syncStatus:    document.getElementById("sync-status"),
  filtroLimpar:  document.getElementById("filtro-limpar"),
  filtroChips:   document.querySelectorAll(".filtro-chip"),
};

/* ----------------------------------------------------------
   ESTADO LOCAL
---------------------------------------------------------- */
let _todasVagas  = [];
let _filtrosAtivos = {};

/* ----------------------------------------------------------
   STATUS DO BACKEND
---------------------------------------------------------- */
async function verificarBackend() {
  const { ok } = await SarAPI.sistema.ping();
  if (ok) {
    el.statusPonto.classList.add("online");
    el.statusTexto.textContent = "backend online";
  } else {
    el.statusPonto.classList.remove("online");
    el.statusPonto.classList.add("offline");
    el.statusTexto.textContent = "backend offline";
  }
}

/* ----------------------------------------------------------
   FORMATAÇÃO
---------------------------------------------------------- */
function _formatarSalario(centavos) {
  if (!centavos || centavos <= 0) return null;
  return (centavos / 100).toLocaleString("pt-BR", {
    style: "currency", currency: "BRL", maximumFractionDigits: 0,
  });
}

function _badgeRegime(tipo) {
  const mapa = { clt: "badge-clt", pj: "badge-pj", estagio: "badge-estagio", estágio: "badge-estagio" };
  const cls  = mapa[(tipo || "").toLowerCase()] || "badge-outro";
  const label = tipo ? tipo.toUpperCase() : "OUTRO";
  return `<span class="badge ${cls}">${label}</span>`;
}

function _badgeModalidade(mod) {
  const mapa = {
    remoto:     "badge-remoto",
    presencial: "badge-presencial",
    hibrido:    "badge-hibrido",
    híbrido:    "badge-hibrido",
  };
  const cls   = mapa[(mod || "").toLowerCase()] || "badge-outro";
  const label = mod ? mod.charAt(0).toUpperCase() + mod.slice(1).toLowerCase() : "—";
  return `<span class="badge ${cls}">${label}</span>`;
}

function _inicialEmpresa(nome) {
  if (!nome) return "?";
  return nome.trim().charAt(0).toUpperCase();
}

function _dataRelativa(iso) {
  if (!iso) return "";
  try {
    const diff = Math.floor((Date.now() - new Date(iso)) / 86400000);
    if (diff === 0) return "Hoje";
    if (diff === 1) return "Ontem";
    if (diff < 7)  return `${diff} dias atrás`;
    if (diff < 30) return `${Math.floor(diff / 7)} sem. atrás`;
    return `${Math.floor(diff / 30)} meses atrás`;
  } catch { return ""; }
}

/* ----------------------------------------------------------
   RENDERIZAÇÃO DO CARD
---------------------------------------------------------- */
function _renderizarCard(v) {
  const salario    = _formatarSalario(v.salario_inicial);
  const salarioHtml = salario
    ? `<div class="card-salario">${salario}</div>`
    : `<div class="card-salario a-combinar">A combinar</div>`;

  const linkHtml = v.link
    ? `<a href="${v.link}" target="_blank" rel="noopener noreferrer"
          class="btn btn-primario" style="font-size:0.75rem;padding:6px 12px;">
         Ver vaga ↗
       </a>`
    : "";

  return `
    <div class="vaga-card">
      <div class="card-topo">
        <div class="card-avatar">${_inicialEmpresa(v.empresa)}</div>
        <div class="card-empresa-wrap">
          <div class="card-empresa">${v.empresa || "Empresa não informada"}</div>
          <div class="card-titulo">${v.titulo}</div>
        </div>
      </div>

      ${v.localizacao ? `
      <div class="card-local">
        <span>📍</span>
        <span>${v.localizacao}</span>
      </div>` : ""}

      <div class="card-badges">
        ${v.tipo_contrato ? _badgeRegime(v.tipo_contrato) : ""}
        ${v.modalidade    ? _badgeModalidade(v.modalidade) : ""}
      </div>

      ${salarioHtml}

      <div class="card-rodape">
        <span class="card-data">${_dataRelativa(v.data_extracao || v.ultima_sincronizacao)}</span>
        ${linkHtml}
      </div>
    </div>
  `;
}

/* ----------------------------------------------------------
   SKELETON LOADER
---------------------------------------------------------- */
function _mostrarSkeleton(qtd) {
  el.vagasGrid.innerHTML = Array.from({ length: qtd }, () => `
    <div class="vaga-card carregando">
      <div class="card-topo">
        <div class="card-avatar skeleton"></div>
        <div class="card-empresa-wrap" style="gap:6px;display:flex;flex-direction:column;">
          <div class="card-empresa skeleton" style="height:12px;width:55%;"></div>
          <div class="card-titulo skeleton" style="height:18px;width:85%;"></div>
        </div>
      </div>
      <div class="card-local skeleton" style="height:12px;width:60%;"></div>
      <div class="card-badges" style="gap:4px;">
        <div class="skeleton" style="height:20px;width:42px;border-radius:999px;"></div>
        <div class="skeleton" style="height:20px;width:72px;border-radius:999px;"></div>
      </div>
      <div class="skeleton" style="height:16px;width:45%;"></div>
      <div class="card-rodape" style="border-top:none;">
        <div class="skeleton" style="height:12px;width:30%;"></div>
        <div class="skeleton" style="height:30px;width:80px;border-radius:10px;"></div>
      </div>
    </div>
  `).join("");
}

/* ----------------------------------------------------------
   ESTADOS DE FEEDBACK
---------------------------------------------------------- */
function _mostrarVazio() {
  el.vagasGrid.innerHTML = `
    <div class="estado-container">
      <div class="estado-icone">📭</div>
      <div class="estado-titulo">Nenhuma vaga encontrada</div>
      <p class="estado-descricao">
        Clique em <strong>Atualizar</strong> para sincronizar com o Peixe 30,
        ou ajuste os filtros aplicados.
      </p>
    </div>`;
}

function _mostrarErro(msg) {
  el.vagasGrid.innerHTML = `
    <div class="estado-container">
      <div class="estado-icone">⚠️</div>
      <div class="estado-titulo">Não foi possível carregar</div>
      <p class="estado-descricao">${msg || "Verifique se o servidor está rodando."}</p>
    </div>`;
}

/* ----------------------------------------------------------
   FILTROS
---------------------------------------------------------- */
function _aplicarFiltros(vagas) {
  return vagas.filter(v => {
    for (const [campo, valor] of Object.entries(_filtrosAtivos)) {
      const campoVaga = (v[campo] || "").toLowerCase();
      if (campoVaga !== valor.toLowerCase()) return false;
    }
    return true;
  });
}

function _renderizarVagas(vagas) {
  const filtradas = _aplicarFiltros(vagas);
  const total     = _todasVagas.length;
  const visiveis  = filtradas.length;

  el.vagasContagem.textContent = total > 0
    ? `${visiveis} de ${total}`
    : "";

  if (!filtradas.length) { _mostrarVazio(); return; }
  el.vagasGrid.innerHTML = filtradas.map(_renderizarCard).join("");
}

function _inicializarFiltros() {
  el.filtroChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const campo = chip.dataset.filtro;
      const valor = chip.dataset.valor;

      if (_filtrosAtivos[campo] === valor) {
        delete _filtrosAtivos[campo];
        chip.classList.remove("ativo");
      } else {
        document.querySelectorAll(`.filtro-chip[data-filtro="${campo}"]`)
          .forEach(c => c.classList.remove("ativo"));
        _filtrosAtivos[campo] = valor;
        chip.classList.add("ativo");
      }

      const temFiltro = Object.keys(_filtrosAtivos).length > 0;
      el.filtroLimpar.classList.toggle("hidden", !temFiltro);
      _renderizarVagas(_todasVagas);
    });
  });

  el.filtroLimpar.addEventListener("click", () => {
    _filtrosAtivos = {};
    el.filtroChips.forEach(c => c.classList.remove("ativo"));
    el.filtroLimpar.classList.add("hidden");
    _renderizarVagas(_todasVagas);
  });
}

/* ----------------------------------------------------------
   CARREGAMENTO DE VAGAS
---------------------------------------------------------- */
async function carregarVagas() {
  _mostrarSkeleton(9);

  const { ok, dados, erro } = await SarAPI.vagas.listar();

  if (!ok) {
    _mostrarErro(erro);
    return;
  }

  _todasVagas = dados || [];
  _renderizarVagas(_todasVagas);
}

/* ----------------------------------------------------------
   SINCRONIZAÇÃO MANUAL
---------------------------------------------------------- */
function _inicializarSync() {
  el.btnSync.addEventListener("click", async () => {
    if (el.btnSync.disabled) return;

    el.btnSync.disabled = true;
    el.btnSync.classList.add("sincronizando");
    el.syncStatus.textContent = "Sincronizando...";

    const { ok, dados } = await SarAPI.vagas.sincronizar();

    if (ok) {
      el.syncStatus.textContent = "Sincronizado ✓";
      setTimeout(() => { el.syncStatus.textContent = ""; }, 4000);
      await carregarVagas();
    } else {
      el.syncStatus.textContent = "Falha na sincronização";
      setTimeout(() => { el.syncStatus.textContent = ""; }, 5000);
    }

    el.btnSync.disabled = false;
    el.btnSync.classList.remove("sincronizando");
  });
}

/* ----------------------------------------------------------
   INICIALIZAÇÃO
---------------------------------------------------------- */
(async () => {
  await verificarBackend();
  _inicializarFiltros();
  _inicializarSync();
  await carregarVagas();
})();

/* ============================================================
   Fim — vagas.js
   ============================================================ */

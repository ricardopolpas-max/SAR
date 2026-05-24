/* ============================================================
   SAR — vagas.js
   Lógica da tela de vagas: listagem, busca, filtros e sincronização.
   ============================================================ */

/* ----------------------------------------------------------
   ELEMENTOS DO DOM
---------------------------------------------------------- */
const el = {
  statusPonto:    document.getElementById("status-ponto"),
  statusTexto:    document.getElementById("status-texto"),
  vagasLista:     document.getElementById("vagas-lista"),
  vagasContagem:  document.getElementById("vagas-contagem"),
  btnSync:        document.getElementById("btn-sync"),
  syncStatus:     document.getElementById("sync-status"),
  filtroLimpar:   document.getElementById("filtro-limpar"),
  filtroChips:     document.querySelectorAll(".filtro-chip"),
  buscaInput:      document.getElementById("busca-input"),
  selectOrdenacao: document.getElementById("select-ordenacao"),
  selectLocalidade: document.getElementById("select-localidade"),
};

/* ----------------------------------------------------------
   ESTADO LOCAL
---------------------------------------------------------- */
let _todasVagas    = [];
let _filtrosAtivos = {};
let _termoBusca    = "";
let _ordenacao     = "recentes";
let _localidade    = "";

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
    if (diff < 7)  return `${diff}d atrás`;
    if (diff < 30) return `${Math.floor(diff / 7)}sem. atrás`;
    return `${Math.floor(diff / 30)}m atrás`;
  } catch { return ""; }
}

/* ----------------------------------------------------------
   RENDERIZAÇÃO — ITEM DE LISTA
---------------------------------------------------------- */
function _renderizarItem(v) {
  const salario     = _formatarSalario(v.salario_inicial);
  const salarioHtml = salario
    ? `<div class="item-salario">${salario}</div>`
    : `<div class="item-salario a-combinar">A combinar</div>`;

  const acoesHtml = `
    <div class="item-acoes">
      <button class="btn btn-secundario btn-item-acao btn-ver-descricao" data-id="${v.id}">Ver descrição</button>
      <button class="btn btn-primario btn-item-acao btn-preparar" data-id="${v.id}">Preparar</button>
    </div>`;

  const empresa = v.empresa || "Empresa não informada";
  const local   = v.localizacao ? ` · 📍 ${v.localizacao}` : "";

  const classeItem = v.disponivel_plataforma
    ? "vaga-item"
    : "vaga-item vaga-removida";

  const removidaBadge = !v.disponivel_plataforma
    ? `<span class="badge" style="background:rgba(245,158,11,.12);color:var(--aviso)">⚠ Removida</span>`
    : "";

  return `
    <div class="${classeItem}">
      <div class="item-avatar">${_inicialEmpresa(v.empresa)}</div>
      <div class="item-info">
        <div class="item-titulo">${v.titulo}</div>
        <div class="item-empresa">${empresa}${local}</div>
      </div>
      <div class="item-badges">
        ${removidaBadge}
        ${v.tipo_contrato ? _badgeRegime(v.tipo_contrato)    : ""}
        ${v.modalidade    ? _badgeModalidade(v.modalidade) : ""}
      </div>
      <div class="item-meta">
        ${salarioHtml}
        <div class="item-data">${_dataRelativa(v.data_extracao || v.ultima_sincronizacao)}</div>
      </div>
      ${acoesHtml}
    </div>
  `;
}

/* ----------------------------------------------------------
   SKELETON LOADER
---------------------------------------------------------- */
function _mostrarSkeleton(qtd) {
  el.vagasLista.innerHTML = Array.from({ length: qtd }, () => `
    <div class="vaga-item">
      <div class="item-avatar skeleton"></div>
      <div class="item-info">
        <div class="skeleton" style="height:14px;width:55%;border-radius:4px;"></div>
        <div class="skeleton" style="height:11px;width:35%;border-radius:4px;margin-top:5px;"></div>
      </div>
      <div class="item-badges" style="gap:4px;">
        <div class="skeleton" style="height:20px;width:40px;border-radius:999px;"></div>
        <div class="skeleton" style="height:20px;width:72px;border-radius:999px;"></div>
      </div>
      <div class="item-meta">
        <div class="skeleton" style="height:13px;width:70px;border-radius:4px;"></div>
        <div class="skeleton" style="height:10px;width:50px;border-radius:4px;margin-top:4px;"></div>
      </div>
      <div class="skeleton" style="height:32px;width:68px;border-radius:8px;flex-shrink:0;"></div>
    </div>
  `).join("");
}

/* ----------------------------------------------------------
   ESTADOS DE FEEDBACK
---------------------------------------------------------- */
function _mostrarVazio() {
  el.vagasLista.innerHTML = `
    <div class="estado-container">
      <div class="estado-icone">📭</div>
      <div class="estado-titulo">Nenhuma vaga encontrada</div>
      <p class="estado-descricao">
        Tente outros termos de busca, ajuste os filtros
        ou clique em <strong>Atualizar</strong> para sincronizar com o Peixe 30.
      </p>
    </div>`;
}

function _mostrarErro(msg) {
  el.vagasLista.innerHTML = `
    <div class="estado-container">
      <div class="estado-icone">⚠️</div>
      <div class="estado-titulo">Não foi possível carregar</div>
      <p class="estado-descricao">${msg || "Verifique se o servidor está rodando."}</p>
    </div>`;
}

/* ----------------------------------------------------------
   BUSCA
---------------------------------------------------------- */
function _filtrarBusca(vagas) {
  if (!_termoBusca) return vagas;
  const t = _termoBusca.toLowerCase();
  return vagas.filter(v =>
    (v.titulo      || "").toLowerCase().includes(t) ||
    (v.empresa     || "").toLowerCase().includes(t) ||
    (v.localizacao || "").toLowerCase().includes(t)
  );
}

/* ----------------------------------------------------------
   ORDENAÇÃO
---------------------------------------------------------- */
function _ordenar(vagas) {
  const c = [...vagas];
  switch (_ordenacao) {
    case "salario":
      return c.sort((a, b) => (b.salario_inicial || 0) - (a.salario_inicial || 0));
    case "empresa":
      return c.sort((a, b) => (a.empresa || "").localeCompare(b.empresa || "", "pt-BR"));
    case "titulo":
      return c.sort((a, b) => (a.titulo || "").localeCompare(b.titulo || "", "pt-BR"));
    default:
      return c.sort((a, b) =>
        (b.ultima_sincronizacao || "") > (a.ultima_sincronizacao || "") ? 1 : -1
      );
  }
}

/* ----------------------------------------------------------
   FILTROS — aplicação e contagem
---------------------------------------------------------- */
function _aplicarFiltros(vagas) {
  return vagas.filter(v => {
    if (_localidade && v.localizacao !== _localidade) return false;
    for (const [campo, valor] of Object.entries(_filtrosAtivos)) {
      if ((v[campo] || "").toLowerCase() !== valor) return false;
    }
    return true;
  });
}

function _atualizarContagensFiltros(vagas) {
  el.filtroChips.forEach(chip => {
    const campo = chip.dataset.filtro;
    const valor = chip.dataset.valor;
    if (!chip.dataset.label) {
      chip.dataset.label = chip.textContent.trim();
    }
    const count = vagas.filter(v => (v[campo] || "").toLowerCase() === valor).length;
    chip.textContent = `${chip.dataset.label} (${count})`;
    chip.style.opacity = count === 0 ? "0.35" : "1";
    chip.style.pointerEvents = count === 0 ? "none" : "";
  });
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
    const mc = document.getElementById("filtro-mobile-contrato");
    const mm = document.getElementById("filtro-mobile-modalidade");
    if (mc) mc.value = "";
    if (mm) mm.value = "";
    _renderizarVagas(_todasVagas);
  });

  /* Filtros mobile — selects sincronizados com _filtrosAtivos */
  const _filtroMobileContrato  = document.getElementById("filtro-mobile-contrato");
  const _filtroMobileModalidade = document.getElementById("filtro-mobile-modalidade");

  function _aplicarFiltroMobile(campo, valor) {
    if (valor) {
      _filtrosAtivos[campo] = valor;
    } else {
      delete _filtrosAtivos[campo];
    }
    _renderizarVagas(_todasVagas);
  }

  if (_filtroMobileContrato) {
    _filtroMobileContrato.addEventListener("change", function () {
      _aplicarFiltroMobile("tipo_contrato", this.value);
    });
  }
  if (_filtroMobileModalidade) {
    _filtroMobileModalidade.addEventListener("change", function () {
      _aplicarFiltroMobile("modalidade", this.value);
    });
  }
}

/* ----------------------------------------------------------
   LOCALIDADE — popular select e filtrar
---------------------------------------------------------- */
function _popularLocalidades(vagas) {
  const atual = el.selectLocalidade.value;
  const localidades = [...new Set(
    vagas.map(v => v.localizacao).filter(Boolean)
  )].sort((a, b) => a.localeCompare(b, "pt-BR"));

  el.selectLocalidade.innerHTML = `<option value="">Todas as localidades</option>` +
    localidades.map(l => `<option value="${l}">${l}</option>`).join("");

  if (localidades.includes(atual)) {
    el.selectLocalidade.value = atual;
  }
}

function _inicializarLocalidade() {
  el.selectLocalidade.addEventListener("change", () => {
    _localidade = el.selectLocalidade.value;
    _renderizarVagas(_todasVagas);
  });
}

/* ----------------------------------------------------------
   BUSCA E ORDENAÇÃO — inicialização
---------------------------------------------------------- */
function _inicializarBusca() {
  let _timer;
  el.buscaInput.addEventListener("input", () => {
    clearTimeout(_timer);
    _timer = setTimeout(() => {
      _termoBusca = el.buscaInput.value.trim();
      _renderizarVagas(_todasVagas);
    }, 250);
  });
}

function _inicializarOrdenacao() {
  el.selectOrdenacao.addEventListener("change", () => {
    _ordenacao = el.selectOrdenacao.value;
    _renderizarVagas(_todasVagas);
  });
}

/* ----------------------------------------------------------
   RENDERIZAÇÃO PRINCIPAL
---------------------------------------------------------- */
function _renderizarVagas(vagas) {
  let resultado = _aplicarFiltros(vagas);
  resultado = _filtrarBusca(resultado);
  resultado = _ordenar(resultado);

  const visiveis = resultado.length;
  const total    = vagas.length;
  el.vagasContagem.textContent = total > 0 ? `${visiveis} de ${total}` : "";

  if (!resultado.length) { _mostrarVazio(); return; }
  el.vagasLista.innerHTML = resultado.map(_renderizarItem).join("");
}

/* ----------------------------------------------------------
   CARREGAMENTO DE VAGAS
---------------------------------------------------------- */
async function carregarVagas() {
  _mostrarSkeleton(12);

  const { ok, dados, erro } = await SarAPI.vagas.listar();

  if (!ok) { _mostrarErro(erro); return; }

  _todasVagas = dados || [];
  _popularLocalidades(_todasVagas);
  _atualizarContagensFiltros(_todasVagas);
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
    el.syncStatus.textContent = "Sincronizando…";

    const { ok, dados } = await SarAPI.vagas.sincronizar();

    el.btnSync.disabled = false;
    el.btnSync.classList.remove("sincronizando");

    if (ok) {
      el.syncStatus.textContent = `Sincronizado ✓ — ${dados.processadas} vagas`;
      setTimeout(() => { el.syncStatus.textContent = ""; }, 5000);
      await carregarVagas();
    } else {
      el.syncStatus.textContent = "Falha na sincronização";
      setTimeout(() => { el.syncStatus.textContent = ""; }, 5000);
    }
  });
}

/* ----------------------------------------------------------
   CICLO DE DISPONIBILIDADE — verifica a cada 20 min
---------------------------------------------------------- */
function _inicializarCicloDisponibilidade() {
  async function _verificar() {
    const { ok, dados } = await SarAPI.vagas.verificarDisponibilidade();
    if (!ok || !dados || !dados.desatualizado) return;
    el.syncStatus.textContent = "⚠ Vagas desatualizadas — clique Atualizar";
  }
  setInterval(_verificar, 20 * 60 * 1000);
}

/* ----------------------------------------------------------
   MODAL — Descrição da Vaga
---------------------------------------------------------- */
let _vagaModalId = null;

function _abrirModalVaga(id) {
  const v = _todasVagas.find(x => x.id === id);
  if (!v) return;
  _vagaModalId = id;

  document.getElementById("modal-vaga-titulo").textContent = v.titulo || "Sem título";
  document.getElementById("modal-vaga-empresa").textContent =
    (v.empresa || "Empresa não informada") + (v.localizacao ? ` · 📍 ${v.localizacao}` : "");

  const salario = _formatarSalario(v.salario_inicial);
  document.getElementById("modal-vaga-badges").innerHTML = [
    v.tipo_contrato ? _badgeRegime(v.tipo_contrato) : "",
    v.modalidade    ? _badgeModalidade(v.modalidade) : "",
    salario ? `<span class="badge">${salario}</span>` : "",
  ].join("");

  const descEl = document.getElementById("modal-vaga-descricao");
  if (v.descricao) {
    descEl.textContent = v.descricao;
  } else {
    descEl.innerHTML = '<em style="color:var(--texto-des)">Descrição não disponível para esta vaga.</em>';
  }

  document.getElementById("modal-score").classList.add("hidden");
  const scoreBtn = document.getElementById("modal-score-btn");
  scoreBtn.textContent = "📊 Ver compatibilidade";
  scoreBtn.disabled = false;

  document.getElementById("modal-vaga").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function _fecharModal() {
  document.getElementById("modal-vaga").classList.add("hidden");
  document.body.style.overflow = "";
}

function _prepararCandidatura(id) {
  const v = _todasVagas.find(x => x.id === id);
  if (!v) return;

  // Reseta estado antes do nav click para que entrarSecaoCurriculos encontre estado correto
  if (typeof iniciarGeracaoCurriculo === "function") {
    iniciarGeracaoCurriculo(id, v.titulo, v.empresa);
  }

  document.querySelector('[data-secao="curriculos"]').click();

  const aviso = document.getElementById("curriculos-aviso-indisponivel");
  if (aviso) aviso.classList.toggle("hidden", !!v.disponivel_plataforma);
}

function _inicializarModal() {
  document.getElementById("modal-fechar").addEventListener("click", _fecharModal);
  document.getElementById("modal-vaga").addEventListener("click", function (e) {
    if (e.target === this) _fecharModal();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") _fecharModal();
  });

  el.vagasLista.addEventListener("click", function (e) {
    const btnVer = e.target.closest(".btn-ver-descricao");
    if (btnVer) {
      _abrirModalVaga(parseInt(btnVer.dataset.id));
      return;
    }
    const btnPreparar = e.target.closest(".btn-preparar");
    if (btnPreparar) {
      const id = parseInt(btnPreparar.dataset.id);
      _prepararCandidatura(id);
    }
  });

  document.getElementById("modal-preparar").addEventListener("click", function () {
    const id = _vagaModalId;
    _fecharModal();
    _prepararCandidatura(id);
  });

  document.getElementById("modal-score-btn").addEventListener("click", async function () {
    if (!_vagaModalId) return;
    this.textContent = "Calculando…";
    this.disabled = true;

    const { ok, dados, erro } = await SarAPI.vagas.score(_vagaModalId);

    this.textContent = "📊 Recalcular";
    this.disabled = false;

    if (!ok) {
      alert("Erro ao calcular compatibilidade:\n" + erro);
      return;
    }

    const scoreEl = document.getElementById("modal-score-valor");
    scoreEl.textContent = `${dados.score}%`;
    scoreEl.className = "score-valor " +
      (dados.score >= 70 ? "alto" : dados.score >= 40 ? "medio" : "baixo");

    document.getElementById("modal-score-resumo").textContent = dados.resumo || "";
    document.getElementById("modal-score-fortes").innerHTML =
      (dados.pontos_fortes || []).map(p => `<li>${p}</li>`).join("");
    document.getElementById("modal-score-lacunas").innerHTML =
      (dados.lacunas || []).map(l => `<li>${l}</li>`).join("");

    document.getElementById("modal-score").classList.remove("hidden");
  });
}

/* ----------------------------------------------------------
   INICIALIZAÇÃO
---------------------------------------------------------- */
(async () => {
  await verificarBackend();
  _inicializarFiltros();
  _inicializarBusca();
  _inicializarOrdenacao();
  _inicializarLocalidade();
  _inicializarSync();
  _inicializarModal();
  _inicializarCicloDisponibilidade();
  await carregarVagas();
})();

/* ============================================================
   Fim — vagas.js
   ============================================================ */

/* ============================================================
   SAR — perfil.js
   Lógica da tela de perfil: formulários, CRUD e renderização.
   ============================================================ */

/* ----------------------------------------------------------
   ELEMENTOS DO DOM
---------------------------------------------------------- */
const el = {
  // Formulários
  formDados:       document.getElementById("form-dados"),
  formContatos:    document.getElementById("form-contatos"),
  formExperiencia: document.getElementById("form-experiencia"),
  formFormacao:    document.getElementById("form-formacao"),
  formHabilidade:  document.getElementById("form-habilidade"),
  formIdioma:      document.getElementById("form-idioma"),
  formCertificacao: document.getElementById("form-certificacao"),
  formDocumento:   document.getElementById("form-documento"),

  // Listas
  listaExperiencias:   document.getElementById("lista-experiencias"),
  listaFormacoes:      document.getElementById("lista-formacoes"),
  listaHabilidades:    document.getElementById("lista-habilidades"),
  listaIdiomas:        document.getElementById("lista-idiomas"),
  listaCertificacoes:  document.getElementById("lista-certificacoes"),
  listaDocumentos:     document.getElementById("lista-documentos"),
};

/* ----------------------------------------------------------
   ESTADO LOCAL
---------------------------------------------------------- */
let _perfilCompleto = null;

/* ----------------------------------------------------------
   RENDERIZAÇÃO — Listas de itens
---------------------------------------------------------- */
function _renderizarLista(items, container, template) {
  if (!items || items.length === 0) {
    container.innerHTML = `<p style="color: var(--texto-sec); font-size: var(--fonte-sm);">Nenhum item adicionado.</p>`;
    return;
  }
  container.innerHTML = items.map(template).join("");
}

function _templateExperiencia(exp) {
  const periodo = exp.data_inicio && exp.data_fim
    ? `${exp.data_inicio} até ${exp.data_fim}`
    : exp.data_inicio ? `Desde ${exp.data_inicio}` : "Data não informada";

  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${exp.cargo} — ${exp.empresa}</div>
        <div class="item-lista-desc">${periodo}</div>
        ${exp.descricao ? `<div class="item-lista-desc" style="margin-top: 4px;">${exp.descricao}</div>` : ""}
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerExperiencia(${exp.id})">Remover</button>
      </div>
    </div>
  `;
}

function _templateFormacao(form) {
  const periodo = form.data_conclusao ? `Concluído em ${form.data_conclusao}` : "Em progresso";
  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${form.curso}</div>
        <div class="item-lista-desc">${form.instituicao} • ${form.nivel}</div>
        <div class="item-lista-desc" style="margin-top: 4px;">${periodo}</div>
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerFormacao(${form.id})">Remover</button>
      </div>
    </div>
  `;
}

function _templateHabilidade(hab) {
  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${hab.nome}</div>
        <div class="item-lista-desc">${hab.proficiencia.charAt(0).toUpperCase() + hab.proficiencia.slice(1)}</div>
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerHabilidade(${hab.id})">Remover</button>
      </div>
    </div>
  `;
}

function _templateIdioma(idio) {
  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${idio.nome}</div>
        <div class="item-lista-desc">${idio.proficiencia.charAt(0).toUpperCase() + idio.proficiencia.slice(1)}</div>
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerIdioma(${idio.id})">Remover</button>
      </div>
    </div>
  `;
}

function _templateCertificacao(cert) {
  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${cert.nome}</div>
        <div class="item-lista-desc">${cert.emissor}</div>
        ${cert.data_emissao ? `<div class="item-lista-desc" style="margin-top: 4px;">Emitida em ${cert.data_emissao}</div>` : ""}
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerCertificacao(${cert.id})">Remover</button>
      </div>
    </div>
  `;
}

function _templateDocumento(doc) {
  return `
    <div class="item-lista">
      <div class="item-lista-info">
        <div class="item-lista-titulo">${doc.nome_arquivo}</div>
        <div class="item-lista-desc">${doc.tipo.replace(/_/g, " ")}</div>
      </div>
      <div class="item-lista-acoes">
        <button onclick="removerDocumento(${doc.id})">Remover</button>
      </div>
    </div>
  `;
}

/* ----------------------------------------------------------
   CARREGAMENTO DE PERFIL
---------------------------------------------------------- */
async function carregarPerfil() {
  const { ok, dados, erro } = await SarAPI.perfil.carregarCompleto();

  if (!ok) {
    console.error("Erro ao carregar perfil:", erro);
    return;
  }

  _perfilCompleto = dados;

  // Popula formulário de dados
  if (dados.perfil) {
    document.getElementById("dados-resumo").value = dados.perfil.resumo_profissional || "";
    document.getElementById("dados-localizacao").value = dados.perfil.localizacao || "";
    document.getElementById("dados-disponibilidade").value = dados.perfil.disponibilidade || "";
    document.getElementById("dados-salario").value = dados.perfil.pretensao_salarial || 0;
  }

  // Popula contatos
  if (dados.contatos) {
    document.getElementById("contatos-telefone").value = dados.contatos.telefone || "";
    document.getElementById("contatos-linkedin").value = dados.contatos.linkedin || "";
    document.getElementById("contatos-github").value = dados.contatos.github || "";
    document.getElementById("contatos-website").value = dados.contatos.website || "";
  }

  // Renderiza listas
  _renderizarLista(dados.experiencias, el.listaExperiencias, _templateExperiencia);
  _renderizarLista(dados.formacoes, el.listaFormacoes, _templateFormacao);
  _renderizarLista(dados.habilidades, el.listaHabilidades, _templateHabilidade);
  _renderizarLista(dados.idiomas, el.listaIdiomas, _templateIdioma);
  _renderizarLista(dados.certificacoes, el.listaCertificacoes, _templateCertificacao);
  _renderizarLista(dados.documentos, el.listaDocumentos, _templateDocumento);
}

/* ----------------------------------------------------------
   EVENTOS — Formulários (criar/atualizar)
---------------------------------------------------------- */
el.formDados.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    resumo_profissional: document.getElementById("dados-resumo").value.trim(),
    localizacao: document.getElementById("dados-localizacao").value.trim(),
    disponibilidade: document.getElementById("dados-disponibilidade").value || null,
    pretensao_salarial: parseInt(document.getElementById("dados-salario").value) || 0,
  };
  const { ok, erro } = await SarAPI.perfil.atualizar(dados);
  if (!ok) {
    alert("Erro ao salvar: " + erro);
  } else {
    alert("Dados salvos com sucesso!");
    await carregarPerfil();
  }
});

el.formContatos.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    telefone: document.getElementById("contatos-telefone").value.trim() || null,
    linkedin: document.getElementById("contatos-linkedin").value.trim() || null,
    github: document.getElementById("contatos-github").value.trim() || null,
    website: document.getElementById("contatos-website").value.trim() || null,
  };
  const { ok, erro } = await SarAPI.perfil.contatos.atualizar(dados);
  if (!ok) {
    alert("Erro ao salvar: " + erro);
  } else {
    alert("Contatos salvos com sucesso!");
    await carregarPerfil();
  }
});

el.formExperiencia.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    cargo: document.getElementById("exp-cargo").value.trim(),
    empresa: document.getElementById("exp-empresa").value.trim(),
    data_inicio: document.getElementById("exp-inicio").value || null,
    data_fim: document.getElementById("exp-fim").value || null,
    em_atual: document.getElementById("exp-atual").checked ? 1 : 0,
    descricao: document.getElementById("exp-descricao").value.trim() || null,
  };
  const { ok, erro } = await SarAPI.perfil.experiencias.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formExperiencia.reset();
    await carregarPerfil();
  }
});

el.formFormacao.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    instituicao: document.getElementById("form-instituicao").value.trim(),
    curso: document.getElementById("form-curso").value.trim(),
    nivel: document.getElementById("form-nivel").value,
    data_inicio: document.getElementById("form-inicio").value || null,
    data_conclusao: document.getElementById("form-conclusao").value || null,
    em_progresso: document.getElementById("form-progresso").checked ? 1 : 0,
  };
  const { ok, erro } = await SarAPI.perfil.formacoes.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formFormacao.reset();
    await carregarPerfil();
  }
});

el.formHabilidade.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    nome: document.getElementById("hab-nome").value.trim(),
    proficiencia: document.getElementById("hab-proficiencia").value,
    categoria: document.getElementById("hab-categoria").value.trim() || null,
  };
  const { ok, erro } = await SarAPI.perfil.habilidades.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formHabilidade.reset();
    await carregarPerfil();
  }
});

el.formIdioma.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    nome: document.getElementById("idio-nome").value.trim(),
    proficiencia: document.getElementById("idio-proficiencia").value,
  };
  const { ok, erro } = await SarAPI.perfil.idiomas.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formIdioma.reset();
    await carregarPerfil();
  }
});

el.formCertificacao.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    nome: document.getElementById("cert-nome").value.trim(),
    emissor: document.getElementById("cert-emissor").value.trim(),
    data_emissao: document.getElementById("cert-emissao").value || null,
    data_expiracao: document.getElementById("cert-expiracao").value || null,
    url: document.getElementById("cert-url").value.trim() || null,
  };
  const { ok, erro } = await SarAPI.perfil.certificacoes.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formCertificacao.reset();
    await carregarPerfil();
  }
});

el.formDocumento.addEventListener("submit", async (e) => {
  e.preventDefault();
  const dados = {
    tipo: document.getElementById("doc-tipo").value,
    nome_arquivo: document.getElementById("doc-nome").value.trim(),
    caminho_disco: document.getElementById("doc-caminho").value.trim(),
  };
  const { ok, erro } = await SarAPI.perfil.documentos.criar(dados);
  if (!ok) {
    alert("Erro: " + erro);
  } else {
    el.formDocumento.reset();
    await carregarPerfil();
  }
});

/* ----------------------------------------------------------
   EVENTOS — Remover itens (funções globais para onclick)
---------------------------------------------------------- */
window.removerExperiencia = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.experiencias.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

window.removerFormacao = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.formacoes.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

window.removerHabilidade = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.habilidades.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

window.removerIdioma = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.idiomas.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

window.removerCertificacao = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.certificacoes.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

window.removerDocumento = async (id) => {
  if (!confirm("Tem certeza que deseja remover?")) return;
  const { ok, erro } = await SarAPI.perfil.documentos.remover(id);
  if (!ok) alert("Erro: " + erro);
  else await carregarPerfil();
};

/* ----------------------------------------------------------
   INICIALIZAÇÃO
---------------------------------------------------------- */
(async () => {
  await carregarPerfil();
})();

/* ============================================================
   Fim — perfil.js
   ============================================================ */

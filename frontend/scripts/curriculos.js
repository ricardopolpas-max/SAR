/* ============================================================
   SAR — curriculos.js
   Geração de currículo personalizado por vaga via IA (Motor 4 Bloco 5).
   ============================================================ */

let _curriculoVagaId     = null;
let _curriculoVagaTitulo  = "";
let _curriculoVagaEmpresa = "";

/* ----------------------------------------------------------
   ESTADOS
---------------------------------------------------------- */
function _mostrarEstadoCurriculo(estado) {
  document.getElementById("curriculos-vazio").classList.toggle("hidden",    estado !== "vazio");
  document.getElementById("curriculos-gerando").classList.toggle("hidden",   estado !== "gerando");
  document.getElementById("curriculos-resultado").classList.toggle("hidden", estado !== "resultado");
}

/* ----------------------------------------------------------
   GERAÇÃO
---------------------------------------------------------- */
async function _gerarCurriculo() {
  if (!_curriculoVagaId) return;

  _mostrarEstadoCurriculo("gerando");
  document.getElementById("curriculos-gerando-titulo").textContent =
    "Gerando currículo para: " + (_curriculoVagaTitulo || "vaga selecionada") + "…";

  const { ok, dados, erro } = await SarAPI.vagas.gerarCurriculo(_curriculoVagaId);

  if (!ok) {
    alert("Erro ao gerar currículo:\n" + erro);
    _mostrarEstadoCurriculo("vazio");
    return;
  }

  const vaga = dados.vaga || {};
  const info = vaga.titulo + (vaga.empresa ? " · " + vaga.empresa : "");
  document.getElementById("curriculos-vaga-info").textContent = info;
  document.getElementById("curriculos-texto").value = dados.curriculo || "";
  _mostrarEstadoCurriculo("resultado");
}

/* ----------------------------------------------------------
   API PÚBLICA — chamada por vagas.js
---------------------------------------------------------- */
function iniciarGeracaoCurriculo(vagaId, vagaTitulo, vagaEmpresa) {
  _curriculoVagaId     = vagaId;
  _curriculoVagaTitulo  = vagaTitulo  || "";
  _curriculoVagaEmpresa = vagaEmpresa || "";
  _gerarCurriculo();
}

/* ----------------------------------------------------------
   BOTÕES
---------------------------------------------------------- */
document.getElementById("btn-curriculo-copiar").addEventListener("click", function () {
  const texto = document.getElementById("curriculos-texto").value;
  if (!texto) return;
  navigator.clipboard.writeText(texto).then(() => {
    this.textContent = "Copiado ✓";
    setTimeout(() => { this.textContent = "Copiar texto"; }, 2000);
  }).catch(() => {
    alert("Não foi possível copiar automaticamente. Selecione o texto manualmente.");
  });
});

document.getElementById("btn-curriculo-regerar").addEventListener("click", _gerarCurriculo);

/* ----------------------------------------------------------
   ESTADO INICIAL
---------------------------------------------------------- */
_mostrarEstadoCurriculo("vazio");

/* ============================================================
   Fim — curriculos.js
   ============================================================ */

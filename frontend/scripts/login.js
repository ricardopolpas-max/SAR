/* ============================================================
   SAR — login.js
   Lógica da tela de acesso ao sistema.
   ============================================================ */

(function () {

  /* Se já há sessão ativa, redireciona direto para o sistema */
  if (SarAPI.autenticacao.estaAutenticado()) {
    window.location.replace("/sar");
    return;
  }

  const formLogin     = document.getElementById("form-login");
  const campoEmail    = document.getElementById("email");
  const campoSenha    = document.getElementById("senha");
  const grupoEmail    = document.getElementById("grupo-email");
  const grupoSenha    = document.getElementById("grupo-senha");
  const erroEmail     = document.getElementById("erro-email");
  const erroSenha     = document.getElementById("erro-senha");
  const avisoGlobal   = document.getElementById("aviso-global");
  const btnEntrar     = document.getElementById("btn-entrar");

  /* ----------------------------------------------------------
     Utilitários de feedback visual
  ---------------------------------------------------------- */
  function limparErros() {
    grupoEmail.classList.remove("com-erro");
    grupoSenha.classList.remove("com-erro");
    erroEmail.textContent = "";
    erroSenha.textContent = "";
    avisoGlobal.textContent = "";
    avisoGlobal.classList.remove("visivel");
  }

  function marcarErro(grupo, campo, mensagem) {
    grupo.classList.add("com-erro");
    campo.textContent = mensagem;
  }

  function exibirAviso(mensagem) {
    avisoGlobal.textContent = mensagem;
    avisoGlobal.classList.add("visivel");
  }

  function definirCarregando(ativo) {
    btnEntrar.disabled = ativo;
    btnEntrar.textContent = ativo ? "Entrando…" : "Entrar";
  }

  /* ----------------------------------------------------------
     Validação local antes de enviar
  ---------------------------------------------------------- */
  function validar(email, senha) {
    let valido = true;

    if (!email) {
      marcarErro(grupoEmail, erroEmail, "Informe o e-mail.");
      valido = false;
    }

    if (!senha) {
      marcarErro(grupoSenha, erroSenha, "Informe a senha.");
      valido = false;
    }

    return valido;
  }

  /* ----------------------------------------------------------
     Submissão
  ---------------------------------------------------------- */
  let _abortController = null;

  formLogin.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    limparErros();

    const email = campoEmail.value.trim();
    const senha = campoSenha.value;

    if (!validar(email, senha)) return;

    if (_abortController) _abortController.abort();
    _abortController = new AbortController();

    definirCarregando(true);

    const resultado = await SarAPI.autenticacao.entrar(email, senha, _abortController.signal);

    if (_abortController.signal.aborted) return;
    _abortController = null;
    definirCarregando(false);

    if (resultado.ok) {
      window.location.replace("/sar");
      return;
    }

    if (resultado.status === 0) {
      exibirAviso("Servidor inacessível. Verifique se o SAR está rodando.");
      return;
    }

    exibirAviso("E-mail ou senha incorretos.");
  });

})();

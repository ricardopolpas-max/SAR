/* ============================================================
   SAR — cadastro.js
   Lógica da tela de criação de conta.
   ============================================================ */

(function () {

  /* Se já há sessão ativa, redireciona direto para o sistema */
  if (SarAPI.autenticacao.estaAutenticado()) {
    window.location.replace("/sar");
    return;
  }

  const formCadastro      = document.getElementById("form-cadastro");
  const campoNome         = document.getElementById("nome");
  const campoEmail        = document.getElementById("email");
  const campoSenha        = document.getElementById("senha");
  const campoConfirmar    = document.getElementById("confirmar-senha");
  const grupoNome         = document.getElementById("grupo-nome");
  const grupoEmail        = document.getElementById("grupo-email");
  const grupoSenha        = document.getElementById("grupo-senha");
  const grupoConfirmar    = document.getElementById("grupo-confirmar-senha");
  const erroNome          = document.getElementById("erro-nome");
  const erroEmail         = document.getElementById("erro-email");
  const erroSenha         = document.getElementById("erro-senha");
  const erroConfirmar     = document.getElementById("erro-confirmar-senha");
  const avisoGlobal       = document.getElementById("aviso-global");
  const btnCadastrar      = document.getElementById("btn-cadastrar");

  /* Eye toggle */
  document.getElementById("olho-senha").addEventListener("click", function () {
    const tipo = campoSenha.type === "password" ? "text" : "password";
    campoSenha.type = tipo;
    this.textContent = tipo === "password" ? "👁" : "🙈";
  });
  document.getElementById("olho-confirmar").addEventListener("click", function () {
    const tipo = campoConfirmar.type === "password" ? "text" : "password";
    campoConfirmar.type = tipo;
    this.textContent = tipo === "password" ? "👁" : "🙈";
  });

  /* ----------------------------------------------------------
     Utilitários de feedback visual
  ---------------------------------------------------------- */
  function limparErros() {
    grupoNome.classList.remove("com-erro");
    grupoEmail.classList.remove("com-erro");
    grupoSenha.classList.remove("com-erro");
    grupoConfirmar.classList.remove("com-erro");
    erroNome.textContent      = "";
    erroEmail.textContent     = "";
    erroSenha.textContent     = "";
    erroConfirmar.textContent = "";
    avisoGlobal.textContent   = "";
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
    btnCadastrar.disabled = ativo;
    btnCadastrar.textContent = ativo ? "Criando conta…" : "Criar conta";
  }

  /* ----------------------------------------------------------
     Validação local antes de enviar
  ---------------------------------------------------------- */
  function validar(nome, email, senha, confirmar) {
    let valido = true;

    if (!nome) {
      marcarErro(grupoNome, erroNome, "Informe o nome completo.");
      valido = false;
    }

    if (!email) {
      marcarErro(grupoEmail, erroEmail, "Informe o e-mail.");
      valido = false;
    }

    if (!senha) {
      marcarErro(grupoSenha, erroSenha, "Informe a senha.");
      valido = false;
    } else if (senha.length < 6) {
      marcarErro(grupoSenha, erroSenha, "A senha deve ter pelo menos 6 caracteres.");
      valido = false;
    }

    if (!confirmar) {
      marcarErro(grupoConfirmar, erroConfirmar, "Confirme a senha.");
      valido = false;
    } else if (senha && confirmar !== senha) {
      marcarErro(grupoConfirmar, erroConfirmar, "As senhas não coincidem.");
      valido = false;
    }

    return valido;
  }

  /* ----------------------------------------------------------
     Submissão
  ---------------------------------------------------------- */
  formCadastro.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    limparErros();

    const nome      = campoNome.value.trim();
    const email     = campoEmail.value.trim();
    const senha     = campoSenha.value;
    const confirmar = campoConfirmar.value;

    if (!validar(nome, email, senha, confirmar)) return;

    definirCarregando(true);

    const resultado = await SarAPI.autenticacao.cadastrar(nome, email, senha);

    definirCarregando(false);

    if (resultado.ok) {
      window.location.replace("/sar");
      return;
    }

    if (resultado.status === 0) {
      exibirAviso("Servidor inacessível. Verifique se o SAR está rodando.");
      return;
    }

    if (resultado.status === 409) {
      marcarErro(grupoEmail, erroEmail, "Este e-mail já está cadastrado.");
      return;
    }

    exibirAviso("Não foi possível criar a conta. Tente novamente.");
  });

})();

/* ============================================================
   SAR — api.js
   Módulo central de comunicação com o backend.
   Todas as chamadas HTTP do sistema passam por aqui.
   ============================================================ */

const SarAPI = (() => {

  /* ----------------------------------------------------------
     CONFIGURAÇÃO
  ---------------------------------------------------------- */
  const BASE_URL = "https://127.0.0.1:8000";

  /* ----------------------------------------------------------
     SESSÃO LOCAL — token armazenado no localStorage
  ---------------------------------------------------------- */
  const _CHAVE_TOKEN = "sar_token";
  const _CHAVE_NOME  = "sar_nome";

  function _obterToken() {
    return localStorage.getItem(_CHAVE_TOKEN);
  }

  function _salvarSessao(token, nome) {
    localStorage.setItem(_CHAVE_TOKEN, token);
    localStorage.setItem(_CHAVE_NOME,  nome);
  }

  function _limparSessao() {
    localStorage.removeItem(_CHAVE_TOKEN);
    localStorage.removeItem(_CHAVE_NOME);
  }

  /* ----------------------------------------------------------
     NÚCLEO — fetch centralizado com tratamento de erros
  ---------------------------------------------------------- */
  async function _requisitar(metodo, rota, corpo = null) {
    const cabecalhos = {
      "Content-Type": "application/json",
      "Accept":       "application/json",
    };

    const token = _obterToken();
    if (token) {
      cabecalhos["Authorization"] = `Bearer ${token}`;
    }

    const opcoes = {
      method:  metodo,
      headers: cabecalhos,
    };

    if (corpo !== null) {
      opcoes.body = JSON.stringify(corpo);
    }

    try {
      const resposta = await fetch(`${BASE_URL}${rota}`, opcoes);

      if (!resposta.ok) {
        const detalhe = await resposta.text();
        return {
          ok:     false,
          status: resposta.status,
          erro:   detalhe || `Erro HTTP ${resposta.status}`,
          dados:  null,
        };
      }

      const dados = await resposta.json();
      return { ok: true, status: resposta.status, dados, erro: null };

    } catch (e) {
      return {
        ok:     false,
        status: 0,
        erro:   "Backend inacessível. Verifique se o servidor está rodando.",
        dados:  null,
      };
    }
  }

  /* ----------------------------------------------------------
     AUTENTICAÇÃO
  ---------------------------------------------------------- */
  const autenticacao = {
    /** Cadastra novo candidato e abre sessão automaticamente. */
    async cadastrar(nome, email, senha) {
      const resultado = await _requisitar("POST", "/auth/cadastrar", { nome, email, senha });
      if (resultado.ok) {
        _salvarSessao(resultado.dados.token, resultado.dados.nome);
      }
      return resultado;
    },

    /** Autentica candidato existente e abre sessão. */
    async entrar(email, senha) {
      const resultado = await _requisitar("POST", "/auth/login", { email, senha });
      if (resultado.ok) {
        _salvarSessao(resultado.dados.token, resultado.dados.nome);
      }
      return resultado;
    },

    /** Encerra sessão no backend e limpa localStorage. */
    async encerrar() {
      const resultado = await _requisitar("POST", "/auth/logout");
      _limparSessao();
      return resultado;
    },

    /** Retorna true se há token válido no localStorage. */
    estaAutenticado() {
      return !!_obterToken();
    },

    /** Retorna o nome do candidato logado (ou string vazia). */
    obterNome() {
      return localStorage.getItem(_CHAVE_NOME) || "";
    },
  };

  /* ----------------------------------------------------------
     CANDIDATO AUTENTICADO
  ---------------------------------------------------------- */
  const candidato = {
    /** Retorna nome e e-mail do candidato logado. */
    async meuPerfil() {
      return _requisitar("GET", "/candidatos/meu-perfil");
    },
  };

  /* ----------------------------------------------------------
     SISTEMA
  ---------------------------------------------------------- */
  const sistema = {
    /** Verifica se o backend está respondendo. */
    async ping() {
      return _requisitar("GET", "/");
    },
  };

  /* ----------------------------------------------------------
     VAGAS
  ---------------------------------------------------------- */
  const vagas = {
    /** Retorna todas as vagas ordenadas por data de extração. */
    async listar() {
      return _requisitar("GET", "/vagas");
    },

    /** Retorna uma vaga pelo ID. */
    async buscar(id) {
      return _requisitar("GET", `/vagas/${id}`);
    },

    /** Cadastra uma nova vaga. */
    async criar(dados) {
      return _requisitar("POST", "/vagas", dados);
    },

    /** Atualiza campos de uma vaga existente. */
    async atualizar(id, dados) {
      return _requisitar("PUT", `/vagas/${id}`, dados);
    },

    /** Remove uma vaga pelo ID. */
    async remover(id) {
      return _requisitar("DELETE", `/vagas/${id}`);
    },

    /** Dispara sincronização manual com o Peixe 30 (background). */
    async sincronizar() {
      return _requisitar("POST", "/vagas/sincronizar");
    },

    /** Retorna o resultado da última sincronização gravado em configuracoes. */
    async ultimaSync() {
      return _requisitar("GET", "/configuracoes/ultima_sincronizacao");
    },
  };

  /* ----------------------------------------------------------
     CONFIGURAÇÕES
  ---------------------------------------------------------- */
  const configuracoes = {
    /** Retorna todas as configurações do sistema. */
    async listar() {
      return _requisitar("GET", "/configuracoes");
    },

    /** Retorna o valor de uma configuração pela chave. */
    async buscar(chave) {
      return _requisitar("GET", `/configuracoes/${chave}`);
    },

    /** Salva ou atualiza uma configuração. */
    async salvar(chave, valor) {
      return _requisitar("POST", "/configuracoes", { chave, valor });
    },
  };

  /* ----------------------------------------------------------
     LOGS
  ---------------------------------------------------------- */
  const logs = {
    /** Retorna os últimos registros do log do sistema. */
    async listar(limite = 50) {
      return _requisitar("GET", `/logs?limite=${limite}`);
    },
  };

  /* ----------------------------------------------------------
     API PÚBLICA
  ---------------------------------------------------------- */
  return {
    base: BASE_URL,
    autenticacao,
    candidato,
    sistema,
    vagas,
    configuracoes,
    logs,
  };

})();

/* Expõe globalmente para uso nos scripts de tela */
window.SarAPI = SarAPI;

/* ============================================================
   Fim — api.js
   ============================================================ */

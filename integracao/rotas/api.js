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

  const HEADERS = {
    "Content-Type": "application/json",
    "Accept":       "application/json",
  };

  /* ----------------------------------------------------------
     NÚCLEO — fetch centralizado com tratamento de erros
  ---------------------------------------------------------- */
  async function _requisitar(metodo, rota, corpo = null) {
    const opcoes = {
      method:  metodo,
      headers: HEADERS,
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

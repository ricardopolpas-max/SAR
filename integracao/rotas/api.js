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
     SESSÃO LOCAL — token armazenado em sessionStorage (morre ao fechar app)
  ---------------------------------------------------------- */
  const _CHAVE_TOKEN = "sar_token";
  const _CHAVE_NOME  = "sar_nome";

  function _obterToken() {
    return sessionStorage.getItem(_CHAVE_TOKEN);
  }

  function _salvarSessao(token, nome) {
    sessionStorage.setItem(_CHAVE_TOKEN, token);
    sessionStorage.setItem(_CHAVE_NOME,  nome);
  }

  function _limparSessao() {
    sessionStorage.removeItem(_CHAVE_TOKEN);
    sessionStorage.removeItem(_CHAVE_NOME);
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
     PERFIL DO CANDIDATO (Motor 3)
  ---------------------------------------------------------- */
  const perfil = {
    // Perfil principal
    async carregar() {
      return _requisitar("GET", "/perfil-candidato");
    },

    async carregarCompleto() {
      return _requisitar("GET", "/perfil-candidato/completo");
    },

    async atualizar(dados) {
      return _requisitar("PUT", "/perfil-candidato", dados);
    },

    async novoManual(dados) {
      return _requisitar("POST", "/perfil-candidato/novo-manual", dados);
    },

    // Experiências
    experiencias: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/experiencias");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/experiencias", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/experiencias/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/experiencias/${id}`);
      },
    },

    // Formações
    formacoes: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/formacoes");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/formacoes", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/formacoes/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/formacoes/${id}`);
      },
    },

    // Habilidades
    habilidades: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/habilidades");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/habilidades", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/habilidades/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/habilidades/${id}`);
      },
    },

    // Idiomas
    idiomas: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/idiomas");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/idiomas", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/idiomas/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/idiomas/${id}`);
      },
    },

    // Certificações
    certificacoes: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/certificacoes");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/certificacoes", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/certificacoes/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/certificacoes/${id}`);
      },
    },

    // Documentos
    documentos: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/documentos");
      },
      async criar(dados) {
        return _requisitar("POST", "/perfil-candidato/documentos", dados);
      },
      async atualizar(id, dados) {
        return _requisitar("PUT", `/perfil-candidato/documentos/${id}`, dados);
      },
      async remover(id) {
        return _requisitar("DELETE", `/perfil-candidato/documentos/${id}`);
      },
    },

    // Contatos
    contatos: {
      async listar() {
        return _requisitar("GET", "/perfil-candidato/contatos");
      },
      async atualizar(dados) {
        return _requisitar("PUT", "/perfil-candidato/contatos", dados);
      },
    },

    // Upload de arquivo (Motor 4)
    async uploadArquivo(arquivo) {
      const formData = new FormData();
      formData.append("arquivo", arquivo);

      const token = _obterToken();
      const cabecalhos = { "Accept": "application/json" };
      if (token) {
        cabecalhos["Authorization"] = `Bearer ${token}`;
      }

      try {
        const resposta = await fetch(`${BASE_URL}/perfil-candidato/upload-arquivo`, {
          method: "POST",
          headers: cabecalhos,
          body: formData,
        });

        if (!resposta.ok) {
          const detalhe = await resposta.text();
          return {
            ok: false,
            status: resposta.status,
            erro: detalhe || `Erro HTTP ${resposta.status}`,
            dados: null,
          };
        }

        const dados = await resposta.json();
        return { ok: true, status: resposta.status, dados, erro: null };
      } catch (e) {
        return {
          ok: false,
          status: 0,
          erro: "Erro ao fazer upload do arquivo.",
          dados: null,
        };
      }
    },

    // Validação
    async validar() {
      return _requisitar("POST", "/perfil-candidato/validar");
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
    perfil,
  };

})();

/* Expõe globalmente para uso nos scripts de tela */
window.SarAPI = SarAPI;

/* ============================================================
   Fim — api.js
   ============================================================ */

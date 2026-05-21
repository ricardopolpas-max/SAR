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
  async function _requisitar(metodo, rota, corpo = null, signal = null) {
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

    if (signal) {
      opcoes.signal = signal;
    }

    try {
      const resposta = await fetch(`${BASE_URL}${rota}`, opcoes);

      if (!resposta.ok) {
        let detalhe = `Erro HTTP ${resposta.status}`;
        try {
          const corpo = await resposta.json();
          detalhe = corpo.detail || corpo.mensagem || corpo.erro || JSON.stringify(corpo);
        } catch (_) {
          detalhe = (await resposta.text()) || detalhe;
        }
        return { ok: false, status: resposta.status, erro: detalhe, dados: null };
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
    async entrar(email, senha, signal = null) {
      const resultado = await _requisitar("POST", "/auth/login", { email, senha }, signal);
      if (resultado.ok) {
        _salvarSessao(resultado.dados.token, resultado.dados.nome);
      }
      return resultado;
    },

    /** Encerra sessão no backend e limpa sessionStorage. */
    async encerrar() {
      const resultado = await _requisitar("POST", "/auth/logout");
      _limparSessao();
      return resultado;
    },

    /** Exclui permanentemente a conta e todos os dados do candidato. */
    async excluirConta(senha) {
      const resultado = await _requisitar("DELETE", "/candidatos/minha-conta", { senha });
      if (resultado.ok) _limparSessao();
      return resultado;
    },

    /** Retorna true se há token válido na sessão atual. */
    estaAutenticado() {
      return !!_obterToken();
    },

    /** Retorna o nome do candidato logado (ou string vazia). */
    obterNome() {
      return sessionStorage.getItem(_CHAVE_NOME) || "";
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

    /** Verifica se o total de vagas disponíveis diverge do Peixe 30. */
    async verificarDisponibilidade() {
      return _requisitar("GET", "/vagas/verificar-disponibilidade");
    },

    /** Calcula score de aderência do candidato para uma vaga via IA. */
    async score(id) {
      return _requisitar("POST", `/vagas/${id}/score`);
    },

    /** Gera currículo personalizado para a vaga via IA (DA-02: salvo automaticamente). */
    async gerarCurriculo(id) {
      return _requisitar("POST", `/vagas/${id}/gerar-curriculo`);
    },

    /** Gera carta de apresentação personalizada para a vaga via IA. */
    async gerarCarta(id) {
      return _requisitar("POST", `/vagas/${id}/gerar-carta`);
    },

    /** Retorna a conversa (histórico + score) do candidato para uma vaga. */
    async carregarConversa(id) {
      return _requisitar("GET", `/vagas/${id}/conversa`);
    },

    /** Envia mensagem do candidato ao Recrutador IA e recebe próxima pergunta ou conclusão. */
    async conversar(id, mensagem) {
      return _requisitar("POST", `/vagas/${id}/conversar`, { mensagem });
    },

    /** Apaga a conversa do candidato para uma vaga (permite reiniciar entrevista). */
    async resetarConversa(id) {
      return _requisitar("DELETE", `/vagas/${id}/conversa`);
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
      async uploadComplementar(arquivo, descricao) {
        const formData = new FormData();
        formData.append("arquivo", arquivo);
        formData.append("descricao", descricao || "");
        const token = _obterToken();
        const cabecalhos = { "Accept": "application/json" };
        if (token) cabecalhos["Authorization"] = `Bearer ${token}`;
        try {
          const resposta = await fetch(
            `${BASE_URL}/perfil-candidato/documentos/upload-complementar`,
            { method: "POST", headers: cabecalhos, body: formData }
          );
          if (!resposta.ok) {
            const detalhe = await resposta.text();
            return { ok: false, status: resposta.status, erro: detalhe, dados: null };
          }
          const dados = await resposta.json();
          return { ok: true, status: resposta.status, dados, erro: null };
        } catch (e) {
          return { ok: false, status: 0, erro: "Erro ao enviar documento.", dados: null };
        }
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

    // Importação via IA — Motor 4
    async importar(arquivo) {
      const formData = new FormData();
      formData.append("arquivo", arquivo);

      const token = _obterToken();
      const cabecalhos = { "Accept": "application/json" };
      if (token) {
        cabecalhos["Authorization"] = `Bearer ${token}`;
      }

      try {
        const resposta = await fetch(`${BASE_URL}/perfil-candidato/importar`, {
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
          erro: "Erro ao enviar currículo para importação.",
          dados: null,
        };
      }
    },

    // Validação
    async validar() {
      return _requisitar("POST", "/perfil-candidato/validar");
    },

    // Lista currículos premium gerados com conteúdo (restauração de sessão)
    async listarCurriculosGerados() {
      return _requisitar("GET", "/perfil-candidato/curriculos-gerados");
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

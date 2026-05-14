/**
 * ALMOX 1.0 - Motor Central do Frontend (SPA)
 * Responsável pelo carregamento de telas e controle de navegação
 * Versão com fallback para login.html - 20/02/2026
 */

const App = (function() {
    'use strict';
    
    // =====================================================
    // ELEMENTOS DO DOM
    // =====================================================
    const elements = {
        container: document.getElementById("container-principal"),
        painelSuperior: document.getElementById("painel-superior"),
        painelLateral: document.getElementById("painel-lateral"),
        btnLogout: document.getElementById("btn-logout"),
        nomeUsuario: document.getElementById("nome-usuario"),
        loginUsuario: document.getElementById("login-usuario-header")
    };

    // =====================================================
    // FUNÇÕES AUXILIARES
    // =====================================================
    
    /**
     * Verifica se o usuário está autenticado
     * @returns {boolean} True se estiver logado
     */
    function estaAutenticado() {
        return window.API && typeof API.estaAutenticado === 'function' 
            ? API.estaAutenticado() 
            : false;
    }

    /**
     * Obtém dados do usuário logado
     * @returns {Object|null} Dados do usuário ou null
     */
    function getUsuarioLogado() {
        return window.API && typeof API.obterSessao === 'function'
            ? API.obterSessao()
            : null;
    }

    /**
     * Atualiza informações do usuário no painel superior
     */
    function atualizarPainelUsuario() {
        const usuario = getUsuarioLogado();
        
        if (!usuario) {
            if (elements.nomeUsuario) elements.nomeUsuario.style.display = 'none';
            if (elements.loginUsuario) elements.loginUsuario.style.display = 'none';
            if (elements.btnLogout) elements.btnLogout.style.display = 'none';
            return;
        }
        
        if (elements.nomeUsuario) {
            elements.nomeUsuario.textContent = usuario.nome || 'Usuário';
            elements.nomeUsuario.style.display = 'inline';
        }
        
        if (elements.loginUsuario) {
            elements.loginUsuario.textContent = `@${usuario.login || 'login'}`;
            elements.loginUsuario.style.display = 'inline';
        }
        
        if (elements.btnLogout) {
            elements.btnLogout.style.display = 'inline';
        }
    }

    /**
     * Carrega os painéis globais (superior e lateral)
     */
    async function carregarPaineisGlobais() {
        if (!estaAutenticado()) {
            if (elements.painelSuperior) elements.painelSuperior.style.display = 'none';
            if (elements.painelLateral) elements.painelLateral.style.display = 'none';
            return;
        }
        
        try {
            if (elements.painelSuperior) {
                elements.painelSuperior.style.display = 'flex';
                atualizarPainelUsuario();
            }
            
            if (elements.painelLateral) {
                elements.painelLateral.style.display = 'block';
            }
            
        } catch (error) {
            console.error('[App] Erro ao carregar painéis:', error);
        }
    }

    // =====================================================
    // FUNÇÃO PRINCIPAL DE CARREGAMENTO DE TELAS
    // =====================================================
    
    /**
     * Carrega uma tela HTML dentro do container principal
     * @param {string} url - Nome do arquivo HTML na pasta 'telas'
     * @param {function} callback - Função opcional a ser executada após o carregamento
     */
    async function carregarTela(url, callback) {
        console.log(`[App] Carregando tela: ${url}`);
        
        const autenticado = estaAutenticado();
        const isTelaLogin = url === 'login.html';
        
        if (!autenticado && !isTelaLogin) {
            console.log('[App] Usuário não autenticado, redirecionando para login');
            window.location.href = '/';
            return;
        }
        
        if (autenticado && isTelaLogin) {
            console.log('[App] Usuário já autenticado, redirecionando para dashboard');
            window.location.href = '/dashboard';
            return;
        }
        
        try {
            const response = await fetch(`telas/${url}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const html = await response.text();
            
            if (elements.container) {
                elements.container.innerHTML = html;
                    // Adiciona endereço e porta ao título do login
                    if (url === 'index.html') {
                        const loginHeader = document.querySelector('.login-header h1');
                        if (loginHeader) {
                            const host = window.location.hostname;
                            const port = window.location.port || '5000';
                            loginHeader.textContent = `ALMOX 1.0 - ${host}:${port}`;
                        }
                    }
            } else {
                console.error('[App] Container principal não encontrado');
                return;
            }
            
            await carregarPaineisGlobais();
            
            if (typeof callback === 'function') {
                callback();
            }
            
            document.dispatchEvent(new CustomEvent('app:telaCarregada', { 
                detail: { url: url } 
            }));
            
        } catch (error) {
            console.error('[App] Erro ao carregar tela:', error);
            
            // =====================================================
            // FALLBACK: Se index.html falhar, tenta login.html
            // =====================================================
            if (url === 'index.html') {
                console.log('[App] ⚠️ Falha no index.html - Tentando fallback para login.html...');
                
                try {
                    // Tenta carregar login.html como fallback
                    const fallbackResponse = await fetch('telas/login.html');
                    
                    if (fallbackResponse.ok) {
                        const fallbackHtml = await fallbackResponse.text();
                        if (elements.container) {
                            elements.container.innerHTML = fallbackHtml;
                            console.log('[App] ✅ Fallback carregado com sucesso');
                            
                            // Dispara evento para o login.js se inicializar
                            document.dispatchEvent(new CustomEvent('app:fallbackAtivado'));
                            return;
                        }
                    }
                    
                    // Se fallback também falhar, redireciona direto
                    console.log('[App] Fallback também falhou - redirecionando...');
                    window.location.href = '/';
                    
                } catch (fallbackError) {
                    console.error('[App] Erro no fallback:', fallbackError);
                    window.location.href = '/';
                }
                
                return;
            }
            
            // Erro genérico para outras telas
            if (elements.container) {
                elements.container.innerHTML = `
                    <div style="
                        display: flex; 
                        flex-direction: column; 
                        align-items: center; 
                        justify-content: center; 
                        min-height: 400px; 
                        color: #e74c3c; 
                        text-align: center;
                        padding: 20px;
                    ">
                        <h2>❌ Falha ao carregar a tela</h2>
                        <p style="margin: 20px 0; color: #666;">
                            Não foi possível carregar "${url}". 
                            Erro: ${error.message}
                        </p>
                        <button onclick="window.location.href='/'" 
                                style="
                                    padding: 10px 20px; 
                                    background: #3498db; 
                                    color: white; 
                                    border: none; 
                                    border-radius: 4px; 
                                    cursor: pointer;
                                ">
                            Voltar ao Início
                        </button>
                    </div>
                `;
            }
        }
    }

    // =====================================================
    // INICIALIZAÇÃO E EVENTOS
    // =====================================================
    
    function configurarEventos() {
        if (elements.btnLogout) {
            elements.btnLogout.addEventListener('click', (e) => {
                e.preventDefault();
                if (window.API && typeof API.logout === 'function') {
                    API.logout();
                } else {
                    localStorage.removeItem('almox_user');
                    window.location.href = '/';
                }
            });
        }
        
        document.addEventListener('app:loginEfetuado', () => {
            carregarPaineisGlobais();
        });
        
        document.addEventListener('app:logoutEfetuado', () => {
            if (elements.painelSuperior) elements.painelSuperior.style.display = 'none';
            if (elements.painelLateral) elements.painelLateral.style.display = 'none';
            carregarTela('login.html');
        });
    }

    /**
     * Inicializa a aplicação
     */
    async function inicializar() {
        console.log('[App] Inicializando ALMOX 1.0...');
        console.log('[App] Servidor base: https://127.0.0.1:5000');
        
        configurarEventos();
        
        const autenticado = estaAutenticado();
        console.log(`[App] Usuário ${autenticado ? 'autenticado' : 'não autenticado'}`);
        
        if (autenticado) {
            await carregarTela('dashboard.html');
        } else {
            await carregarTela('index.html');
        }
        
        console.log('[App] ALMOX 1.0 inicializado com sucesso');
    }

    // =====================================================
    // API PÚBLICA
    // =====================================================
    
    inicializar().catch(error => {
        console.error('[App] Erro fatal na inicialização:', error);
        
        if (elements.container) {
            elements.container.innerHTML = `
                <div style="color: #e74c3c; padding: 40px; text-align: center;">
                    <h2>❌ Erro Fatal</h2>
                    <p>Não foi possível iniciar o sistema.</p>
                    <p style="color: #666; font-size: 14px;">${error.message}</p>
                    <button onclick="window.location.href='/'" 
                            style="margin-top: 20px; padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Tentar Recarregar
                    </button>
                </div>
            `;
        }
    });

    return {
        carregarTela
    };
})();

if (typeof window !== 'undefined') {
    window.App = App;
    // Prompt para encerrar servidores ao fechar o frontend
    window.addEventListener('beforeunload', async function(event) {
        // Mensagem customizada não é mais suportada em todos browsers, mas o prompt será exibido
        var msg = 'Deseja encerrar os servidores backend ao sair?';
        event.returnValue = msg;
        // Pergunta ao usuário
        var encerrar = confirm('Deseja encerrar os servidores backend ao sair?');
        if (encerrar) {
            // Chama endpoint backend para parar servidores
            try {
                await fetch('/api/parar_servidores', { method: 'POST' });
            } catch (e) {
                // Ignora erro, pois o frontend está fechando
            }
        }
        // Não impede o fechamento
    });
}
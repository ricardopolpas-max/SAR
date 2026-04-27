# =============================================================
# criar_fase1.ps1 - SAR Fase 1: Estrutura e Arquivos
# Executa em: D:\Projetos_VS_Code\Aplicativo_DPT
# Uso: Abra o PowerShell na raiz do projeto e rode:
#      .\criar_fase1.ps1
# =============================================================

$raiz = "D:\Projetos_VS_Code\Aplicativo_DPT"

Write-Host "`n[SAR] Iniciando criacao da estrutura Fase 1...`n" -ForegroundColor Yellow

# --- CRIAR PASTAS ---
$pastas = @(
    "$raiz\frontend\telas",
    "$raiz\frontend\scripts",
    "$raiz\frontend\estilos",
    "$raiz\backend\nucleos",
    "$raiz\backend\rotinas",
    "$raiz\integracao\rotas",
    "$raiz\apoio",
    "$raiz\documentacao"
)

foreach ($pasta in $pastas) {
    if (-not (Test-Path $pasta)) {
        New-Item -ItemType Directory -Path $pasta -Force | Out-Null
        Write-Host "[CRIADA]  $pasta" -ForegroundColor Green
    } else {
        Write-Host "[OK]      $pasta" -ForegroundColor Gray
    }
}

# --- principal.html ---
@'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAR - Sistema de Automacao de Recolocacao</title>
    <link rel="stylesheet" href="../estilos/estilos.css">
</head>
<body>
    <header class="cabecalho">
        <h1>SAR</h1>
        <p class="subtitulo">Sistema de Automacao de Recolocacao</p>
    </header>

    <main class="conteudo-principal">
        <section class="painel-status">
            <h2>Status do Sistema</h2>
            <div id="status-conexao" class="status-badge">Verificando conexao...</div>
        </section>

        <section class="painel-vagas">
            <h2>Vagas Disponiveis</h2>
            <div id="lista-vagas">
                <p class="mensagem-carregando">Carregando vagas...</p>
            </div>
        </section>
    </main>

    <footer class="rodape">
        <p>SAR &copy; 2026 &mdash; Todos os direitos reservados</p>
    </footer>

    <script src="../scripts/principal.js"></script>
</body>
</html>
'@ | Out-File -FilePath "$raiz\frontend\telas\principal.html" -Encoding UTF8
Write-Host "[ARQUIVO] frontend\telas\principal.html" -ForegroundColor Cyan

# --- estilos.css ---
@'
/* estilos.css - CSS Global do SAR - Design System unico */

:root {
  --cor-primaria: #2563EB; --cor-primaria-hover: #1D4ED8; --cor-primaria-suave: #EFF6FF;
  --cor-secundaria: #0F172A; --cor-destaque: #06B6D4;
  --cor-fundo: #F8FAFC; --cor-superficie: #FFFFFF;
  --cor-borda: #E2E8F0; --cor-borda-forte: #CBD5E1;
  --cor-texto-principal: #0F172A; --cor-texto-secundario: #475569;
  --cor-texto-fraco: #94A3B8; --cor-texto-inverso: #FFFFFF;
  --cor-sucesso: #10B981; --cor-sucesso-suave: #ECFDF5;
  --cor-alerta: #F59E0B; --cor-alerta-suave: #FFFBEB;
  --cor-erro: #EF4444; --cor-erro-suave: #FEF2F2;
  --cor-info: #3B82F6; --cor-info-suave: #EFF6FF;
  --fonte-principal: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --fonte-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --tamanho-xs: 0.75rem; --tamanho-sm: 0.875rem; --tamanho-base: 1rem;
  --tamanho-lg: 1.125rem; --tamanho-xl: 1.25rem; --tamanho-2xl: 1.5rem;
  --tamanho-3xl: 1.875rem; --tamanho-4xl: 2.25rem;
  --peso-normal: 400; --peso-medio: 500; --peso-semi: 600; --peso-negrito: 700;
  --espaco-1: 0.25rem; --espaco-2: 0.5rem; --espaco-3: 0.75rem;
  --espaco-4: 1rem; --espaco-5: 1.25rem; --espaco-6: 1.5rem;
  --espaco-8: 2rem; --espaco-10: 2.5rem; --espaco-12: 3rem;
  --raio-sm: 0.375rem; --raio-base: 0.5rem; --raio-lg: 0.75rem;
  --raio-xl: 1rem; --raio-full: 9999px;
  --sombra-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --sombra-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --sombra-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --transicao-rapida: 150ms ease; --transicao-base: 200ms ease; --transicao-suave: 300ms ease;
  --largura-maxima: 1280px; --altura-cabecalho: 64px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body { font-family: var(--fonte-principal); font-size: var(--tamanho-base); font-weight: var(--peso-normal); line-height: 1.6; color: var(--cor-texto-principal); background-color: var(--cor-fundo); -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
img, svg, video { display: block; max-width: 100%; }
a { color: var(--cor-primaria); text-decoration: none; transition: color var(--transicao-rapida); }
a:hover { color: var(--cor-primaria-hover); }
ul, ol { list-style: none; }
button { cursor: pointer; font-family: inherit; border: none; background: none; }
input, select, textarea { font-family: inherit; font-size: inherit; }

h1, h2, h3, h4, h5, h6 { font-weight: var(--peso-semi); line-height: 1.3; color: var(--cor-texto-principal); }
h1 { font-size: var(--tamanho-3xl); font-weight: var(--peso-negrito); }
h2 { font-size: var(--tamanho-2xl); }
h3 { font-size: var(--tamanho-xl); }
h4 { font-size: var(--tamanho-lg); }
p  { color: var(--cor-texto-secundario); line-height: 1.7; }
.subtitulo { font-size: var(--tamanho-sm); color: var(--cor-texto-fraco); font-weight: var(--peso-normal); letter-spacing: 0.01em; }

.cabecalho { position: sticky; top: 0; z-index: 100; height: var(--altura-cabecalho); background-color: var(--cor-superficie); border-bottom: 1px solid var(--cor-borda); box-shadow: var(--sombra-xs); display: flex; align-items: center; padding: 0 var(--espaco-8); gap: var(--espaco-3); }
.cabecalho h1 { font-size: var(--tamanho-xl); font-weight: var(--peso-negrito); color: var(--cor-primaria); letter-spacing: -0.02em; }

.conteudo-principal { max-width: var(--largura-maxima); margin: 0 auto; padding: var(--espaco-8); display: flex; flex-direction: column; gap: var(--espaco-8); }

.rodape { text-align: center; padding: var(--espaco-8); border-top: 1px solid var(--cor-borda); margin-top: var(--espaco-12); }
.rodape p { font-size: var(--tamanho-xs); color: var(--cor-texto-fraco); }

.painel-status, .painel-vagas { background-color: var(--cor-superficie); border: 1px solid var(--cor-borda); border-radius: var(--raio-xl); padding: var(--espaco-6); box-shadow: var(--sombra-sm); }
.painel-status h2, .painel-vagas h2 { font-size: var(--tamanho-lg); font-weight: var(--peso-semi); color: var(--cor-texto-principal); margin-bottom: var(--espaco-4); padding-bottom: var(--espaco-3); border-bottom: 1px solid var(--cor-borda); }

.status-badge { display: inline-flex; align-items: center; gap: var(--espaco-2); padding: var(--espaco-2) var(--espaco-4); border-radius: var(--raio-full); font-size: var(--tamanho-sm); font-weight: var(--peso-medio); background-color: var(--cor-alerta-suave); color: var(--cor-alerta); border: 1px solid #FCD34D; transition: all var(--transicao-base); }
.status-badge::before { content: ''; width: 8px; height: 8px; border-radius: var(--raio-full); background-color: currentColor; animation: pulsar 1.5s infinite; }
.status-badge.conectado { background-color: var(--cor-sucesso-suave); color: var(--cor-sucesso); border-color: #6EE7B7; }
.status-badge.conectado::before { animation: none; }
.status-badge.erro { background-color: var(--cor-erro-suave); color: var(--cor-erro); border-color: #FCA5A5; }
@keyframes pulsar { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

.mensagem-carregando { color: var(--cor-texto-fraco); font-size: var(--tamanho-sm); text-align: center; padding: var(--espaco-8) 0; }
.mensagem-vazia { text-align: center; padding: var(--espaco-10) 0; color: var(--cor-texto-fraco); font-size: var(--tamanho-sm); }

.card-vaga { display: flex; flex-direction: column; gap: var(--espaco-2); padding: var(--espaco-4) var(--espaco-5); border: 1px solid var(--cor-borda); border-radius: var(--raio-lg); background-color: var(--cor-superficie); transition: border-color var(--transicao-base), box-shadow var(--transicao-base), transform var(--transicao-base); cursor: pointer; }
.card-vaga:hover { border-color: var(--cor-primaria); box-shadow: var(--sombra-md); transform: translateY(-1px); }
.card-vaga + .card-vaga { margin-top: var(--espaco-3); }
.card-vaga .titulo-vaga { font-size: var(--tamanho-base); font-weight: var(--peso-semi); color: var(--cor-texto-principal); }
.card-vaga .empresa-vaga { font-size: var(--tamanho-sm); color: var(--cor-texto-secundario); }
.card-vaga .meta-vaga { display: flex; align-items: center; gap: var(--espaco-3); margin-top: var(--espaco-1); }

.tag-status { display: inline-flex; align-items: center; padding: var(--espaco-1) var(--espaco-3); border-radius: var(--raio-full); font-size: var(--tamanho-xs); font-weight: var(--peso-medio); text-transform: uppercase; letter-spacing: 0.05em; }
.tag-status.pendente  { background: var(--cor-alerta-suave);  color: var(--cor-alerta);  }
.tag-status.aprovado  { background: var(--cor-sucesso-suave); color: var(--cor-sucesso); }
.tag-status.reprovado { background: var(--cor-erro-suave);    color: var(--cor-erro);    }
.score-vaga { font-size: var(--tamanho-xs); color: var(--cor-texto-fraco); }
.data-vaga  { font-size: var(--tamanho-xs); color: var(--cor-texto-fraco); margin-left: auto; }

.btn { display: inline-flex; align-items: center; justify-content: center; gap: var(--espaco-2); padding: var(--espaco-2) var(--espaco-5); border-radius: var(--raio-base); font-size: var(--tamanho-sm); font-weight: var(--peso-medio); transition: all var(--transicao-rapida); white-space: nowrap; }
.btn-primario { background-color: var(--cor-primaria); color: var(--cor-texto-inverso); box-shadow: var(--sombra-xs); }
.btn-primario:hover { background-color: var(--cor-primaria-hover); box-shadow: var(--sombra-sm); transform: translateY(-1px); }
.btn-secundario { background-color: var(--cor-superficie); color: var(--cor-texto-principal); border: 1px solid var(--cor-borda-forte); }
.btn-secundario:hover { background-color: var(--cor-fundo); border-color: var(--cor-primaria); color: var(--cor-primaria); }
.btn-ghost { color: var(--cor-primaria); background: transparent; }
.btn-ghost:hover { background-color: var(--cor-primaria-suave); }

.campo { display: flex; flex-direction: column; gap: var(--espaco-1); }
.campo label { font-size: var(--tamanho-sm); font-weight: var(--peso-medio); color: var(--cor-texto-principal); }
.campo input, .campo select, .campo textarea { width: 100%; padding: var(--espaco-2) var(--espaco-3); border: 1px solid var(--cor-borda-forte); border-radius: var(--raio-base); font-size: var(--tamanho-sm); color: var(--cor-texto-principal); background-color: var(--cor-superficie); transition: border-color var(--transicao-rapida), box-shadow var(--transicao-rapida); outline: none; }
.campo input:focus, .campo select:focus, .campo textarea:focus { border-color: var(--cor-primaria); box-shadow: 0 0 0 3px rgb(37 99 235 / 0.1); }
.campo input::placeholder, .campo textarea::placeholder { color: var(--cor-texto-fraco); }

.alerta { display: flex; align-items: flex-start; gap: var(--espaco-3); padding: var(--espaco-4); border-radius: var(--raio-lg); font-size: var(--tamanho-sm); border-width: 1px; border-style: solid; }
.alerta.info    { background: var(--cor-info-suave);    color: var(--cor-info);    border-color: #BFDBFE; }
.alerta.sucesso { background: var(--cor-sucesso-suave); color: var(--cor-sucesso); border-color: #A7F3D0; }
.alerta.alerta  { background: var(--cor-alerta-suave);  color: var(--cor-alerta);  border-color: #FDE68A; }
.alerta.erro    { background: var(--cor-erro-suave);    color: var(--cor-erro);    border-color: #FECACA; }

.oculto { display: none !important; } .visivel { display: block !important; }
.flex { display: flex; } .flex-centro { display: flex; align-items: center; justify-content: center; }
.gap-2 { gap: var(--espaco-2); } .gap-4 { gap: var(--espaco-4); }
.texto-centro { text-align: center; } .w-full { width: 100%; }
.mt-4 { margin-top: var(--espaco-4); } .mt-6 { margin-top: var(--espaco-6); } .mb-4 { margin-bottom: var(--espaco-4); }

@media (max-width: 768px) {
  .conteudo-principal { padding: var(--espaco-4); gap: var(--espaco-5); }
  .cabecalho { padding: 0 var(--espaco-4); }
  h1 { font-size: var(--tamanho-2xl); } h2 { font-size: var(--tamanho-xl); }
}
@media (max-width: 480px) {
  .conteudo-principal { padding: var(--espaco-3); }
  .painel-status, .painel-vagas { padding: var(--espaco-4); }
  .card-vaga .meta-vaga { flex-wrap: wrap; }
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--cor-fundo); }
::-webkit-scrollbar-thumb { background: var(--cor-borda-forte); border-radius: var(--raio-full); }
::-webkit-scrollbar-thumb:hover { background: var(--cor-texto-fraco); }
::selection { background-color: var(--cor-primaria); color: var(--cor-texto-inverso); }
'@ | Out-File -FilePath "$raiz\frontend\estilos\estilos.css" -Encoding UTF8
Write-Host "[ARQUIVO] frontend\estilos\estilos.css" -ForegroundColor Cyan

# --- principal.js ---
@'
// frontend/scripts/principal.js
// Comportamento da tela principal do SAR.
// Responsavel por: verificar conexao com o servidor e carregar vagas.

const URL_BASE = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', () => {
    verificarConexao();
    carregarVagas();
});

async function verificarConexao() {
    const badge = document.getElementById('status-conexao');
    try {
        const resposta = await fetch(`${URL_BASE}/`);
        const dados = await resposta.json();
        if (resposta.ok && dados.status === 'operacional') {
            badge.textContent = 'Servidor operacional';
            badge.classList.add('conectado');
        } else {
            badge.textContent = 'Resposta inesperada do servidor';
            badge.classList.add('erro');
        }
    } catch (erro) {
        badge.textContent = 'Servidor inacessivel — verifique se esta rodando';
        badge.classList.add('erro');
        console.error('[SAR] Falha na conexao:', erro);
    }
}

async function carregarVagas() {
    const container = document.getElementById('lista-vagas');
    try {
        const resposta = await fetch(`${URL_BASE}/vagas`);
        if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
        const vagas = await resposta.json();
        renderizarVagas(vagas, container);
    } catch (erro) {
        container.innerHTML = '<p class="mensagem-vazia">Nao foi possivel carregar as vagas.</p>';
        console.error('[SAR] Falha ao carregar vagas:', erro);
    }
}

function renderizarVagas(vagas, container) {
    if (!vagas || vagas.length === 0) {
        container.innerHTML = '<p class="mensagem-vazia">Nenhuma vaga cadastrada ainda.</p>';
        return;
    }
    container.innerHTML = vagas.map(vaga => `
        <div class="card-vaga">
            <span class="titulo-vaga">${vaga.titulo}</span>
            <span class="empresa-vaga">${vaga.empresa || 'Empresa nao informada'}</span>
            <div class="meta-vaga">
                <span class="tag-status ${(vaga.status || 'PENDENTE').toLowerCase()}">${vaga.status || 'PENDENTE'}</span>
                <span class="score-vaga">Score: ${vaga.score != null ? vaga.score.toFixed(1) : '&mdash;'}</span>
                <span class="data-vaga">${formatarData(vaga.data_extracao)}</span>
            </div>
        </div>
    `).join('');
}

function formatarData(dataISO) {
    if (!dataISO) return '&mdash;';
    try {
        return new Date(dataISO).toLocaleDateString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });
    } catch { return dataISO; }
}

// Fim do arquivo principal.js
'@ | Out-File -FilePath "$raiz\frontend\scripts\principal.js" -Encoding UTF8
Write-Host "[ARQUIVO] frontend\scripts\principal.js" -ForegroundColor Cyan

# --- RESUMO ---
Write-Host "`n[SAR] Fase 1 criada com sucesso!`n" -ForegroundColor Yellow
Write-Host "Proximos passos manuais:" -ForegroundColor White
Write-Host "  1. Mover servidor.py de frontend\scripts\ para backend\" -ForegroundColor Gray
Write-Host "  2. Abrir terminal em backend\ e rodar: uvicorn servidor:app --reload" -ForegroundColor Gray
Write-Host "  3. Abrir frontend\telas\principal.html no browser" -ForegroundColor Gray
Write-Host "  4. Badge verde = handshake OK = Fase 1 certificada!`n" -ForegroundColor Gray

# ============================================================
# SAR - Script de Reestruturação de Pastas
# Governança v2 — Execução única, sem perda de dados
# ============================================================

$raiz = "D:\Projetos_VS_Code\Aplicativo_DPT"

Write-Host "`n[SAR] Iniciando reestruturação de pastas..." -ForegroundColor Cyan

# 1. Criar subpastas do /frontend
$subpastasFrontend = @("telas", "estilos", "scripts")
foreach ($pasta in $subpastasFrontend) {
    $caminho = "$raiz\frontend\$pasta"
    if (-Not (Test-Path $caminho)) {
        New-Item -ItemType Directory -Path $caminho | Out-Null
        Write-Host "[OK] Criado: frontend\$pasta" -ForegroundColor Green
    } else {
        Write-Host "[JA EXISTE] frontend\$pasta" -ForegroundColor Yellow
    }
}

# 2. Criar /integracao na raiz com subpasta /rotas
$pastasIntegracao = @("integracao", "integracao\rotas")
foreach ($pasta in $pastasIntegracao) {
    $caminho = "$raiz\$pasta"
    if (-Not (Test-Path $caminho)) {
        New-Item -ItemType Directory -Path $caminho | Out-Null
        Write-Host "[OK] Criado: $pasta" -ForegroundColor Green
    } else {
        Write-Host "[JA EXISTE] $pasta" -ForegroundColor Yellow
    }
}

# 3. Mover conteúdo de /apoio/integracao para /integracao (raiz)
$origemIntegracao = "$raiz\apoio\integracao"
$destinoIntegracao = "$raiz\integracao"

if (Test-Path $origemIntegracao) {
    $itens = Get-ChildItem -Path $origemIntegracao
    if ($itens.Count -gt 0) {
        foreach ($item in $itens) {
            Move-Item -Path $item.FullName -Destination $destinoIntegracao -Force
            Write-Host "[MOVIDO] apoio\integracao\$($item.Name) -> integracao\" -ForegroundColor Green
        }
    } else {
        Write-Host "[INFO] apoio\integracao estava vazia, nada a mover." -ForegroundColor DarkGray
    }

    # Remove a pasta vazia após migração
    Remove-Item -Path $origemIntegracao -Force
    Write-Host "[OK] Removido: apoio\integracao (pasta vazia)" -ForegroundColor Green
} else {
    Write-Host "[INFO] apoio\integracao nao encontrada, nada a migrar." -ForegroundColor DarkGray
}

# 4. Exibir estrutura final
Write-Host "`n[SAR] Estrutura final:" -ForegroundColor Cyan
tree $raiz

Write-Host "`n[SAR] Reestruturacao concluida com sucesso." -ForegroundColor Cyan

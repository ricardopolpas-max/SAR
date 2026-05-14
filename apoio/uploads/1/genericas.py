# backend/rotinas/genericas.py
# Rotinas genéricas de CRUD (Create, Read, Update, Delete)
# Objetivo: Abstrair SQL repetitivo dos formulários de negócio, centralizando
# a lógica de persistência e garantindo o uso de Prepared Statements (Segurança).
#
# REFATORADO: Agora utiliza EXCLUSIVAMENTE o cliente WebSocket (Ukiceker)
# para comunicação com o banco de dados, via `conecta_cliente.py`.

import sys
import uuid
from pathlib import Path

# Adiciona raiz ao path para garantir importação correta
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from integracao.clientes.conecta_cliente import executar_transacao, executar_consulta
except ImportError:
    # Fallback ou erro explícito se não encontrar
    raise ImportError("Não foi possível importar 'executar_transacao' de 'integracao.clientes.conecta_cliente'")

def selecionar(tabela, campos="*", condicao=None, ordem=None, unico=False):
    """
    Executa um comando SELECT genérico via WebSocket usando SQL Raw.
    """
    if isinstance(campos, list):
        campos_str = ", ".join(campos)
    else:
        campos_str = campos

    sql = f"SELECT {campos_str} FROM {tabela}"
    params = []

    if condicao:
        filtros = []
        for k, v in condicao.items():
            filtros.append(f"{k} = %s")
            params.append(v)
        sql += " WHERE " + " AND ".join(filtros)
        
    if ordem:
        sql += f" ORDER BY {ordem}"
        
    if unico:
        sql += " LIMIT 1"
        
    # 2. Execução via SQL Raw (Protocolo suportado pelo servidor)
    resultado = executar_consulta(sql, params)
    
    if resultado.get("status") == "erro":
        return resultado

    # 3. Normalização do Retorno (Mapear colunas -> dict)
    # Suporte a "rows"/"columns" (servidor nativo) e "linhas"/"colunas" (backend pt-br)
    linhas = resultado.get("linhas") or resultado.get("rows") or []
    colunas = resultado.get("colunas") or resultado.get("columns") or []
    
    lista_dados = []
    if colunas and linhas:
        for linha in linhas:
            if isinstance(linha, list):
                lista_dados.append(dict(zip(colunas, linha)))
            elif isinstance(linha, dict):
                # Se já vier como lista de dicts (padrão do servidor novo)
                lista_dados.append(linha)
            else:
                 pass # formato desconhecido
    elif linhas:
        # Se só tem linhas (lista de dicts sem colunas separadas)
        lista_dados = linhas
        
    if unico:
        return lista_dados[0] if lista_dados else None
        
    return lista_dados

def inserir(tabela, dados):
    """
    Executa um comando INSERT via WebSocket usando transaction_request.
    
    Args:
        tabela (str): Nome da tabela.
        dados (dict): Dicionário {coluna: valor} a ser inserido.
    """
    # Prepara payload para transaction_request
    dados_com_tabela = {"tabela": tabela, **dados}
    
    return executar_transacao("inserir", dados_com_tabela)

def atualizar(tabela, dados, condicao):
    """
    Executa um comando UPDATE via WebSocket usando transaction_request.
    
    Args:
        tabela (str): Nome da tabela.
        dados (dict): Dicionário {coluna: valor} com os novos valores.
        condicao (dict): Dicionário {coluna: valor} para a cláusula WHERE.
    """
    if not condicao:
        raise Exception("Atualização requer uma condição de segurança (WHERE).")
    
    # Prepara payload para transaction_request
    # O protocolo ukiceker espera "acao", "tabela", "dados" e "condicao"
    
    # TRUQUE DE COMPATIBILIDADE (FIX UPDATE ID):
    # O servidor Ukiceker padrão espera que o ID do registro esteja DENTRO de 'dados' para montar o WHERE.
    # Ex: UPDATE ... SET ... WHERE ID = dados['ID']
    # Então, se a condição for ID, injetamos no payload de dados.
    dados_envio = dados.copy()
    if "ID" in condicao:
        dados_envio["ID"] = condicao["ID"]
    elif "id" in condicao:
        dados_envio["id"] = condicao["id"]
        
    # Mantém 'condicao' no payload para servidores que suportam (Patch Híbrido),
    # mas o 'dados_envio' com ID garante que servidor legado funcione.
    payload_final = {"tabela": tabela, **dados_envio, "condicao": condicao}
    
    return executar_transacao("atualizar", payload_final)

# =========================================================
# GENÉRICAS DE ACL MODULAR (Reutilizável em todos os módulos)
# =========================================================

def listar_modulos(ativo=None):
    """
    Lista módulos (genérico, reutilizável).
    Agora implementa a REGRA DE OURO PLUG-AND-PLAY: 
    Só retorna módulos que possuam diretório físico em 'modulos_autonomos'.
    """
    condicao = {}
    if ativo:
        condicao['ativo'] = ativo
    
    modulos_db = selecionar(
        'modulos',
        campos=['id', 'nome', 'descricao', 'icone', 'ordem', 'slug'], # slug é o nome da pasta
        condicao=condicao,
        ordem='ordem ASC'
    )

    if not modulos_db:
        return []

    # Lista de slugs considerados 'Core' (não residem em modulos_autonomos)
    MODULOS_CORE = ['usuarios', 'cargos', 'produtos', 'fornecedores', 'unidades', 'categorias', 'relatorios']

    # Verificação física de diretórios (Descoberta Dinâmica)
    modulos_validos = []
    PATH_MODULOS = ROOT_DIR / "modulos_autonomos"

    for mod in modulos_db:
        slug = mod.get('slug')
        if not slug:
            # Fallback para o nome em lowercase
            slug = str(mod.get('nome', '')).lower().replace(' ', '_')
        
        # Se for Core, é sempre válido (está na estrutura base)
        if slug in MODULOS_CORE:
            modulos_validos.append(mod)
            continue

        caminho_fisico = PATH_MODULOS / slug
        if caminho_fisico.exists() and caminho_fisico.is_dir():
            modulos_validos.append(mod)
        else:
            print(f"[Plug-and-Play] Módulo '{mod.get('nome')}' ('{slug}') cadastrado no DB mas ausente em: {caminho_fisico}")

    return modulos_validos

def obter_permissoes_usuario(id):
    """
    Obtém permissões de um usuário (id_modulo, não id_recurso).
    
    Args:
        id (str): ID do usuário
    
    Returns:
        list: Lista de dicts {id, id_usuario, id_modulo, id_acao}
    """
    sql = """
        SELECT p.id, p.id_usuario, p.id_modulo, p.id_acao
        FROM permissoes_usuario p
        WHERE p.id_usuario = %s
        ORDER BY p.id_modulo, p.id_acao
    """
    resultado = executar_consulta(sql, [id])
    
    if resultado.get("status") == "erro":
        return []
    
    return resultado.get('rows') or resultado.get('linhas') or []

def salvar_permissoes_usuario(id, permissoes_list):
    """
    Salva permissões de um usuário (substitui todas as antigas).
    
    Args:
        id (str): ID do usuário
        permissoes_list (list): Lista de dicts {id_modulo, id_acao}
    
    Returns:
        dict: {status, mensagem, total}
    """
    try:
        permissoes_normais = {
            (str(perm.get('id_modulo')), str(perm.get('id_acao')))
            for perm in (permissoes_list or [])
            if perm.get('id_modulo') and perm.get('id_acao')
        }

        permissoes_atuais = obter_permissoes_usuario(id)
        permissoes_atuais_normais = {
            (str(perm.get('id_modulo')), str(perm.get('id_acao')))
            for perm in (permissoes_atuais or [])
            if perm.get('id_modulo') and perm.get('id_acao')
        }

        if permissoes_normais == permissoes_atuais_normais:
            return {
                "status": "ok",
                "mensagem": "Permissões já estavam atualizadas",
                "total": len(permissoes_normais)
            }

        # 1. Deletar permissões antigas (exclusão individual por ID)
        from integracao.clientes.conecta_cliente import executar_transacao
        permissoes_atuais = obter_permissoes_usuario(id)
        erros = []
        for perm in permissoes_atuais:
            perm_id = perm.get('id')
            if perm_id:
                resultado_del = executar_transacao("excluir", {"tabela": "permissoes_usuario", "dados": {"ID": perm_id}})
                if resultado_del.get("status") != "ok":
                    erros.append(f"ID {perm_id}: {resultado_del.get('mensagem')}")
        if erros:
            return {
                "status": "erro",
                "mensagem": f"Erro ao excluir permissões antigas: {'; '.join(erros)}"
            }
        
        # 2. Inserir novas permissões
        total_inseridas = 0
        for id_modulo, id_acao in permissoes_normais:
            dados = {
                'id': str(uuid.uuid4()),
                'id_usuario': id,
                'id_modulo': id_modulo,
                'id_acao': id_acao
            }
            inserir('permissoes_usuario', dados)
            total_inseridas += 1
        
        return {
            "status": "ok",
            "mensagem": "Permissões salvas com sucesso",
            "total": total_inseridas
        }
    except Exception as e:
        return {
            "status": "erro",
            "mensagem": f"Erro ao salvar permissões: {str(e)}"
        }
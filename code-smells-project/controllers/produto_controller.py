from config import Config
from models import produto as produto_model


class ProdutoController:

    @staticmethod
    def listar():
        return produto_model.get_todos_produtos()

    @staticmethod
    def buscar_por_id(id):
        produto = produto_model.get_produto_por_id(id)
        if not produto:
            raise ValueError("Produto não encontrado")
        return produto

    @staticmethod
    def buscar(termo, categoria, preco_min, preco_max):
        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)
        return produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)

    @staticmethod
    def _validar_dados(dados):
        if not dados:
            raise ValueError("Dados inválidos")

        nome = dados.get("nome")
        preco = dados.get("preco")
        estoque = dados.get("estoque")

        if nome is None:
            raise ValueError("Nome é obrigatório")
        if preco is None:
            raise ValueError("Preço é obrigatório")
        if estoque is None:
            raise ValueError("Estoque é obrigatório")
        if preco < 0:
            raise ValueError("Preço não pode ser negativo")
        if estoque < 0:
            raise ValueError("Estoque não pode ser negativo")
        if len(nome) < 2:
            raise ValueError("Nome muito curto")
        if len(nome) > 200:
            raise ValueError("Nome muito longo")

        categoria = dados.get("categoria", "geral")
        if categoria not in Config.VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida. Válidas: {Config.VALID_CATEGORIES}")

        return {
            "nome": nome,
            "descricao": dados.get("descricao", ""),
            "preco": preco,
            "estoque": estoque,
            "categoria": categoria
        }

    @staticmethod
    def criar(dados):
        validado = ProdutoController._validar_dados(dados)
        produto_id = produto_model.criar_produto(**validado)
        return {"id": produto_id}

    @staticmethod
    def atualizar(id, dados):
        if not produto_model.get_produto_por_id(id):
            raise ValueError("Produto não encontrado")
        validado = ProdutoController._validar_dados(dados)
        produto_model.atualizar_produto(id, **validado)

    @staticmethod
    def deletar(id):
        if not produto_model.get_produto_por_id(id):
            raise ValueError("Produto não encontrado")
        produto_model.deletar_produto(id)

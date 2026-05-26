import enum


class StatusCliente(enum.Enum):
    ATIVO     = "Ativo"
    INATIVO   = "Inativo"
    PROSPECTO = "Prospecto"
    BLOQUEADO = "Bloqueado"


class Escolaridade(enum.Enum):
    FUNDAMENTAL   = "Fundamental"
    MEDIO         = "Médio"
    SUPERIOR      = "Superior"
    POS_GRADUACAO = "Pós-graduação"


class TipoImovel(enum.Enum):
    RESIDENCIAL = "Residencial"
    COMERCIAL   = "Comercial"
    RURAL       = "Rural"
    INDUSTRIAL  = "Industrial"


class OrigemLead(enum.Enum):
    INDICACAO = "Indicação"
    GOOGLE    = "Google"
    INSTAGRAM = "Instagram"
    FACEBOOK  = "Facebook"
    WHATSAPP  = "WhatsApp"
    SITE      = "Site"
    EVENTO    = "Evento"
    OUTROS    = "Outros"


class TipoPessoa(enum.Enum):
    PF = "PF"
    PJ = "PJ"

class CategoriaProduto(enum.Enum):
    PAINEL    = "Painel"
    INVERSOR  = "Inversor"
    CABO      = "Cabo"
    ESTRUTURA = "Estrutura"
    ACESSORIO = "Acessório"
    SERVICO   = "Serviço"


class UnidadeProduto(enum.Enum):
    UN  = "UN"
    M   = "M"
    KG  = "KG"
    KWP = "KWP"

class StatusVenda(enum.Enum):
    ORCAMENTO   = "Orçamento"
    NEGOCIACAO  = "Negociação"
    APROVADO    = "Aprovado"
    EM_ANDAMENTO = "Em Andamento"
    CONCLUIDO   = "Concluído"
    CANCELADO   = "Cancelado"


class FormaPagamento(enum.Enum):
    PIX          = "PIX"
    BOLETO       = "Boleto"
    DINHEIRO     = "Dinheiro"
    CARTAO       = "Cartão"
    FINANCIAMENTO = "Financiamento"


class TipoContrato(enum.Enum):
    CLT      = "CLT"
    AUTONOMO = "Autônomo"
    PJ       = "PJ"


class StatusColaborador(enum.Enum):
    ATIVO   = "Ativo"
    INATIVO = "Inativo"

class TipoMovimento(enum.Enum):
    ENTRADA          = "Entrada"
    SAIDA            = "Saída"
    AJUSTE_POSITIVO  = "Ajuste+"
    AJUSTE_NEGATIVO  = "Ajuste-"

class TipoLancamento(enum.Enum):
    RECEITA = "Receita"
    DESPESA = "Despesa"


class CategoriaFinanceiro(enum.Enum):
    VENDA_EQUIPAMENTOS = "Venda Equipamentos"
    SERVICO_INSTALACAO = "Serviço Instalação"
    MANUTENCAO         = "Manutenção"
    COMISSAO           = "Comissão"
    FORNECEDOR         = "Fornecedor"
    SALARIO            = "Salário"
    ALUGUEL            = "Aluguel"
    MARKETING          = "Marketing"
    IMPOSTO            = "Imposto"
    OUTRAS             = "Outras"


class StatusPagamento(enum.Enum):
    PENDENTE  = "Pendente"
    PAGO      = "Pago"
    ATRASADO  = "Atrasado"
    CANCELADO = "Cancelado"

class StatusPrestacao(enum.Enum):
    PENDENTE  = "Pendente"
    PAGA      = "Paga"
    CANCELADA = "Cancelada"


class StatusProjeto(enum.Enum):
    EM_ANALISE         = "Em Análise"
    APROVADO           = "Aprovado"
    APROVADO_COM_OBRAS = "Aprovado c/ Obras"
    FALTA_TRT          = "Falta TRT"
    CANCELADO          = "Cancelado"


class StatusVistoria(enum.Enum):
    NAO_SOLICITADO = "Não Solicitado"
    SOLICITADO     = "Solicitado"
    REALIZADO      = "Realizado"


class TipoServico(enum.Enum):
    PREVENTIVA = "Preventiva"
    CORRETIVA  = "Corretiva"
    LIMPEZA    = "Limpeza"
    INSPECAO   = "Inspeção"
    GARANTIA   = "Garantia"
    OUTROS     = "Outros"


class StatusOS(enum.Enum):
    ABERTA       = "Aberta"
    EM_ANDAMENTO = "Em Andamento"
    CONCLUIDA    = "Concluída"
    CANCELADA    = "Cancelada"


class PerfilUsuario(enum.Enum):
    ADMIN    = "Admin"
    VENDEDOR = "Vendedor"

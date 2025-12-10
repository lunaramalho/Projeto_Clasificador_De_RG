import csv
import random
from faker import Faker
from datetime import date, timedelta
# from unidecode import unidecode  # opcional: remova acentos se quiser

fake = Faker('pt_BR')


BR_STATE_ABBR = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
    "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
]

BR_STATE_FULL = {
    "AC": "Estado do Acre",
    "AL": "Estado de Alagoas",
    "AP": "Estado do Amapá",
    "AM": "Estado do Amazonas",
    "BA": "Estado da Bahia",
    "CE": "Estado do Ceará",
    "DF": "Distrito Federal",
    "ES": "Estado do Espírito Santo",
    "GO": "Estado de Goiás",
    "MA": "Estado do Maranhão",
    "MT": "Estado de Mato Grosso",
    "MS": "Estado de Mato Grosso do Sul",
    "MG": "Estado de Minas Gerais",
    "PA": "Estado do Pará",
    "PB": "Estado da Paraíba",
    "PR": "Estado do Paraná",
    "PE": "Estado de Pernambuco",
    "PI": "Estado do Piauí",
    "RJ": "Estado do Rio de Janeiro",
    "RN": "Estado do Rio Grande do Norte",
    "RS": "Estado do Rio Grande do Sul",
    "RO": "Estado de Rondônia",
    "RR": "Estado de Roraima",
    "SC": "Estado de Santa Catarina",
    "SP": "Estado de São Paulo",
    "SE": "Estado de Sergipe",
    "TO": "Estado do Tocantins"
}

def add_years_safe(d: date, years: int) -> date:
    """Adiciona anos a uma data tratando ano bissexto (29/02)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d + timedelta(days=years * 365)

def calcular_digito_verificador(cpf_parcial: list) -> int:
    """Calcula o dígito verificador do CPF."""
    tamanho = len(cpf_parcial) + 1
    soma = sum(d * (tamanho - i) for i, d in enumerate(cpf_parcial, start=1))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto

def gerar_cpf(formatted: bool = True, unique_set: set | None = None) -> str:
    """Gera um CPF válido e opcionalmente único."""
    tentativa = 0
    while True:
        tentativa += 1
        cpf_base = [random.randint(0, 9) for _ in range(9)]
        d1 = calcular_digito_verificador(cpf_base)
        d2 = calcular_digito_verificador(cpf_base + [d1])
        cpf_nums = cpf_base + [d1, d2]
        cpf_str_digits = ''.join(str(d) for d in cpf_nums)

        if unique_set is None or cpf_str_digits not in unique_set:
            if unique_set is not None:
                unique_set.add(cpf_str_digits)
            break
        if tentativa > 1000:
            break

    return f"{cpf_str_digits[0:3]}.{cpf_str_digits[3:6]}.{cpf_str_digits[6:9]}-{cpf_str_digits[9:11]}" if formatted else cpf_str_digits

def limpar_titulo(nome: str) -> str:
    """Remove títulos como 'Dr.', 'Dra.', 'Sr.', 'Sra.', 'Srta.' dos nomes."""
    titulos = ["Dr.", "Dra.", "Sr.", "Sra.", "Srta.", "Prof.", "Profa."]
    for t in titulos:
        nome = nome.replace(t, "").strip()
    return nome

def gerar_registro(existing_cpfs: set):
    """Gera um registro completo e realista de identidade."""

    # Nome completo e filiação sem títulos
    nome_completo = limpar_titulo(fake.name())
    filiacao_pai = limpar_titulo(fake.name_male())
    filiacao_mae = limpar_titulo(fake.name_female())

    # Data de nascimento: entre 1 e 90 anos
    data_nascimento = fake.date_of_birth(minimum_age=1, maximum_age=90)

    # Sexo aleatório
    sexo = random.choice(["M", "F"])

    # Naturalidade
    cidade_naturalidade = fake.city()
    estado_nat = random.choice(BR_STATE_ABBR)
    naturalidade = f"{cidade_naturalidade} - {estado_nat}"

    # Local de emissão (cidade e estado)
    cidade_emissao = fake.city()
    estado_emissao = random.choice(BR_STATE_ABBR)

    # Datas: emissão e validade
    dias_atras = random.randint(0, 15 * 365)
    data_emissao = date.today() - timedelta(days=dias_atras)
    validade_anos = random.randint(5, 10)
    validade = add_years_safe(data_emissao, validade_anos)

    # Órgão emissor
    sufixo_tipo = random.choices(["", "SSP", "PC"], weights=[0.4, 0.35, 0.25], k=1)[0]
    orgao = "Instituto de Identificacao" if sufixo_tipo == "" else f"Instituto de Identificacao / {sufixo_tipo} {estado_emissao}"

    # CPF único
    cpf = gerar_cpf(formatted=True, unique_set=existing_cpfs)

    # Nome completo do estado de emissão
    estado_completo_emissao = BR_STATE_FULL.get(estado_emissao, "")

    # Datas formatadas
    fmt = lambda d: d.strftime("%d/%m/%Y")

    registro = {
        "nome_completo": nome_completo,
        "filiacao_pai": filiacao_pai,
        "filiacao_mae": filiacao_mae,
        "data_nascimento": fmt(data_nascimento),
        "sexo": sexo,
        "naturalidade": naturalidade,
        "local_tirou_cidade": cidade_emissao,
        "local_tirou_estado": estado_emissao,
        "estado_completo": estado_completo_emissao,
        "data_emissao": fmt(data_emissao),
        "validade_identidade": fmt(validade),
        "orgao_emissor": orgao,
        "cpf": cpf
    }

    return registro

def gerar_csv(qtd_itens, nome_arquivo="dados_fakes_identidade.csv"):
    """Gera o CSV com os registros simulados."""
    campos = [
        "nome_completo",
        "filiacao_pai",
        "filiacao_mae",
        "data_nascimento",
        "sexo",
        "naturalidade",
        "local_tirou_cidade",
        "local_tirou_estado",
        "estado_completo",
        "data_emissao",
        "validade_identidade",
        "orgao_emissor",
        "cpf"
    ]

    existing_cpfs = set()

    # UTF-8 com BOM para Excel abrir corretamente
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8-sig') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        for _ in range(qtd_itens):
            escritor.writerow(gerar_registro(existing_cpfs))

    print(f"{qtd_itens} registros salvos em '{nome_arquivo}'")

if __name__ == "__main__":
    qtd = int(input("Quantos registros deseja gerar? "))
    gerar_csv(qtd)

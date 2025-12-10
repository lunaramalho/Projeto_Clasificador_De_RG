import csv
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def gerar_imagens(quantidade_imagens, imagem_frente, imagem_verso,
                  csv_arquivo, json_frente, json_verso):
    """
    Gera pares de imagens (frente e trás) de identidades
    com base em dados do CSV e posições do JSON.
    As saídas são salvas em pastas separadas: RGFRENTE e RGTRAS.
    """

    try:
        fonte_bold = ImageFont.truetype("arialbd.ttf", 17)
        fonte_normal = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        # Fontes padrão para sistemas Linux/macOS
        fonte_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
        fonte_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)

    cor_fonte = (0, 0, 0)  # Preto (#000000)

    # Pastas de saída separadas
    pasta_frente = "RGFRENTE"
    pasta_tras = "RGTRAS"
    os.makedirs(pasta_frente, exist_ok=True)
    os.makedirs(pasta_tras, exist_ok=True)

    # --- 1. Ler CSV ---
    with open(csv_arquivo, newline='', encoding='utf-8-sig') as f:
        dados_csv = list(csv.DictReader(f))

    # --- 2. Ler posições ---
    with open(json_frente, encoding='utf-8') as f:
        posicoes_frente = json.load(f)

    with open(json_verso, encoding='utf-8') as f:
        posicoes_verso = json.load(f)

    # --- 3. Limitar quantidade ---
    quantidade_imagens = min(quantidade_imagens, len(dados_csv))

    # --- 4. Gerar as imagens ---
    for id_item, dado in enumerate(dados_csv[:quantidade_imagens], start=1):

        # ======= FRENTE =======
        img_frente = Image.open(imagem_frente).convert("RGB")
        draw_frente = ImageDraw.Draw(img_frente)

        campos_frente = [
            "nome_completo", "cpf", "sexo", "data_nascimento",
            "naturalidade", "validade_identidade", "estado_completo"
        ]

        for campo in campos_frente:
            if campo in posicoes_frente and campo in dado:
                posicoes = posicoes_frente[campo]

                # Se for uma lista de listas (múltiplas posições)
                if isinstance(posicoes[0], list):
                    for x, y in posicoes:
                        fonte = fonte_normal if campo == "estado_completo" else fonte_bold
                        draw_frente.text((x, y), dado[campo], font=fonte, fill=cor_fonte)
                else:
                    # Apenas uma posição
                    x, y = posicoes
                    fonte = fonte_normal if campo == "estado_completo" else fonte_bold
                    draw_frente.text((x, y), dado[campo], font=fonte, fill=cor_fonte)

        caminho_frente = os.path.join(pasta_frente, f"rg-frente_{id_item:04d}.jpg")
        img_frente.save(caminho_frente, "JPEG")

        # ======= TRÁS =======
        img_verso = Image.open(imagem_verso).convert("RGB")
        draw_verso = ImageDraw.Draw(img_verso)

        campos_verso = [
            "filiacao_pai",
            "filiacao_mae",
            "local_tirou_cidade",
            "data_emissao",
            "orgao_emissor"
        ]

        for campo in campos_verso:
            if campo in posicoes_verso and campo in dado:
                posicoes = posicoes_verso[campo]

                if isinstance(posicoes[0], list):
                    for x, y in posicoes:
                        draw_verso.text((x, y), dado[campo], font=fonte_bold, fill=cor_fonte)
                else:
                    x, y = posicoes
                    draw_verso.text((x, y), dado[campo], font=fonte_bold, fill=cor_fonte)

        caminho_verso = os.path.join(pasta_tras, f"rg-tras_{id_item:04d}.jpg")
        img_verso.save(caminho_verso, "JPEG")

    print(f"{quantidade_imagens} frentes salvas em '{pasta_frente}' e {quantidade_imagens} versos em '{pasta_tras}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python gera_dados_sinteticos.py <quantidade_imagens>")
        sys.exit(1)

    quantidade_imagens = int(sys.argv[1])

    gerar_imagens(
        quantidade_imagens=quantidade_imagens,
        imagem_frente="rg_frente.png",
        imagem_verso="rg_atras.png",
        csv_arquivo="dados_fakes_identidade.csv",
        json_frente="posicoes_frente.json",
        json_verso="posicoes_atras.json"
    )


if __name__ == "__main__":
    main()

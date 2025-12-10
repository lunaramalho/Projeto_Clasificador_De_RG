import os
import csv
from PIL import Image

# ==== CONFIGURAÇÕES ====
PASTA_RG = "RGFRENTE"
PASTA_MASCULINO = "faces_m"
PASTA_FEMININO = "faces_f"
CSV_ARQUIVO = "dados_fakes_identidade.csv"

# ✅ NOVA POSIÇÃO DA FOTO NO RG
POS_X = 276
POS_Y = 615
LARGURA_FOTO = 180
ALTURA_FOTO = 220


def carregar_fotos(pasta):
    arquivos = sorted([
        os.path.join(pasta, f)
        for f in os.listdir(pasta)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])
    return arquivos


def main():
    fotos_m = carregar_fotos(PASTA_MASCULINO)
    fotos_f = carregar_fotos(PASTA_FEMININO)

    if not fotos_m or not fotos_f:
        print(" As pastas faces_m ou faces_f estão vazias!")
        return

    with open(CSV_ARQUIVO, newline='', encoding="utf-8-sig") as f:
        dados = list(csv.DictReader(f))

    contador_m = 0
    contador_f = 0

    for i, pessoa in enumerate(dados, start=1):
        sexo = pessoa.get("sexo", "").upper()

        caminho_rg = os.path.join(PASTA_RG, f"rg-frente_{i:04d}.jpg")

        if not os.path.exists(caminho_rg):
            print(f" RG não encontrado: {caminho_rg}")
            continue

        # Escolhe a foto de acordo com o sexo
        if sexo == "F":
            foto_path = fotos_f[contador_f % len(fotos_f)]
            contador_f += 1
        else:
            foto_path = fotos_m[contador_m % len(fotos_m)]
            contador_m += 1

        # Abre RG e Foto
        rg = Image.open(caminho_rg).convert("RGB")
        foto = Image.open(foto_path).convert("RGB")
        foto = foto.resize((LARGURA_FOTO, ALTURA_FOTO))

        #  Cola a foto na NOVA posição
        rg.paste(foto, (POS_X, POS_Y))

        # Salva novamente
        rg.save(caminho_rg, "JPEG")

        print(f" Foto aplicada em: {caminho_rg}")

    print("\n Todas as fotos foram aplicadas com sucesso!")


if __name__ == "__main__":
    main()

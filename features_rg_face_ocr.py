import cv2
import os
import pandas as pd
import numpy as np
import re
from paddleocr import PaddleOCR



PASTA_RAIZ = os.path.join(os.path.expanduser("~"), "Downloads", "Projeto_carteira_de_identidade")

PASTAS = {
    "RG_FRENTE": "RGFRENTE_AUG",
    "RG_VERSO": "RGTRAS_AUG",
}

CSV_SAIDA = "features_rg_face_ocr.csv"

ocr = PaddleOCR(lang="pt")

def extrair_texto(img):
    """
    Extrai todo o texto da imagem usando PaddleOCR (versão nova).
    """
    resultado = ocr.predict(img)
    linhas = []

    # Estrutura retornada:
    # [[ [coords], (texto, confianca) ], ...]
    for bloco in resultado:
        for item in bloco:
            texto_linha = item[1][0]
            linhas.append(texto_linha)

    return " ".join(linhas)

# =========================
# DETECTOR DE ROSTO
# =========================
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(cascade_path)

# =========================
# EXTRAÇÃO DOS CAMPOS DO RG
# =========================
def extrair_dados_textuais(texto):
    dados = {
        "nome_completo": "N/A",
        "numero_rg": "N/A",
        "data_nascimento": "N/A",
        "data_emissao": "N/A",
        "filiacao": "N/A",
    }

    # Número do RG ou CPF (mínimo 9 dígitos)
    rg_match = re.search(r'\b\d{9,11}\b', texto)
    if rg_match:
        dados["numero_rg"] = rg_match.group()

    # Datas no formato DD/MM/AAAA
    datas = re.findall(r'\d{2}/\d{2}/\d{4}', texto)
    if len(datas) >= 1:
        dados["data_nascimento"] = datas[0]
    if len(datas) >= 2:
        dados["data_emissao"] = datas[1]

    # Nome completo (heurística simples: linha longa em maiúsculo)
    linhas = texto.split("\n")
    for linha in linhas:
        if len(linha.split()) >= 2 and linha.isupper():
            dados["nome_completo"] = linha.strip()
            break

    return dados

# =========================
# EXTRAÇÃO DAS FEATURES
# =========================
def extrair_features_imagem(caminho, tipo_documento):
    img = cv2.imread(caminho)

    if img is None:
        return None

    altura, largura, _ = img.shape
    proporcao = largura / altura

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    brilho_medio = np.mean(img_gray)
    contraste = np.std(img_gray)
    blur = cv2.Laplacian(img_gray, cv2.CV_64F).var()

    # =========================
    # DETECÇÃO DE ROSTO (SÓ NA FRENTE)
    # =========================
    rosto_detectado = 0
    area_face = 0

    if tipo_documento == "RG_FRENTE":
        faces = face_cascade.detectMultiScale(img_gray, 1.1, 4)

        if len(faces) > 0:
            x, y, w, h = faces[0]
            rosto_detectado = 1
            area_face = (w * h) / (largura * altura)

    # =========================
    # OCR + EXTRAÇÃO DE CAMPOS
    # =========================
    texto = extrair_texto(img)
    dados_textuais = extrair_dados_textuais(texto)

    return {
        "arquivo": os.path.basename(caminho),
        "tipo_documento": tipo_documento,

        # FEATURES VISUAIS
        "largura": largura,
        "altura": altura,
        "proporcao": round(proporcao, 4),
        "brilho_medio": round(brilho_medio, 2),
        "contraste": round(contraste, 2),
        "nitidez_blur": round(blur, 2),

        # FACE
        "rosto_detectado": rosto_detectado,
        "area_face_norm": round(area_face, 4),

        # CAMPOS DO RG
        **dados_textuais
    }

# =========================
# MAIN
# =========================
def main():
    resultados = []

    for tipo, nome_pasta in PASTAS.items():
        caminho_pasta = os.path.join(PASTA_RAIZ, nome_pasta)

        if not os.path.isdir(caminho_pasta):
            print(f"❌ Pasta não encontrada: {caminho_pasta}")
            continue

        print(f"📂 Lendo imagens de: {nome_pasta}")

        for arquivo in os.listdir(caminho_pasta):
            if arquivo.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
                caminho_img = os.path.join(caminho_pasta, arquivo)

                features = extrair_features_imagem(caminho_img, tipo)

                if features:
                    resultados.append(features)

    if resultados:
        df = pd.DataFrame(resultados)
        df.to_csv(CSV_SAIDA, index=False, encoding="utf-8")
        print(f"\n✅ CSV gerado com sucesso: {CSV_SAIDA}")
        print(f"📊 Total de imagens processadas: {len(df)}")
    else:
        print("⚠️ Nenhuma imagem foi processada.")

if __name__ == "__main__":
    main()

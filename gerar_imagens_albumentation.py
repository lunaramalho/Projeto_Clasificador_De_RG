import cv2
import albumentations as A
import os


PASTA_FRENTE = "RGFRENTE"
PASTA_TRAS = "RGTRAS"

PASTA_FRENTE_SAIDA = "RGFRENTE_AUG"
PASTA_TRAS_SAIDA = "RGTRAS_AUG"

os.makedirs(PASTA_FRENTE_SAIDA, exist_ok=True)
os.makedirs(PASTA_TRAS_SAIDA, exist_ok=True)

transformacao = A.Compose([

    # Iluminação
    A.RandomBrightnessContrast(
        brightness_limit=0.25,
        contrast_limit=0.25,
        p=0.8
    ),

    # Nitidez variável
    A.Sharpen(alpha=(0.1, 0.3), lightness=(0.8, 1.2), p=0.3),

    # Desfoque
    A.GaussianBlur(blur_limit=(3, 7), p=0.3),
    A.MotionBlur(blur_limit=5, p=0.3),

    # Ruído
    A.GaussNoise(var_limit=(5.0, 30.0), p=0.3),

    # Rotação leve (documento levemente torto)
    A.Rotate(limit=3, border_mode=cv2.BORDER_REPLICATE, p=0.5),

    # Perspectiva
    A.Perspective(scale=(0.03, 0.07), p=0.3),

    # Compressão tipo WhatsApp
    A.ImageCompression(quality_lower=35, quality_upper=80, p=0.5),

    # Sombra artificial
    A.RandomShadow(p=0.3)
])

# ===== FUNÇÃO PARA PROCESSAR UMA PASTA =====
def processar_pasta(pasta_entrada, pasta_saida):
    arquivos = os.listdir(pasta_entrada)

    for arquivo in arquivos:
        caminho_arquivo = os.path.join(pasta_entrada, arquivo)

        imagem = cv2.imread(caminho_arquivo)

        if imagem is None:
            print(f"⚠ Erro ao ler: {arquivo}")
            continue

        imagem_aumentada = transformacao(image=imagem)["image"]

        caminho_saida = os.path.join(pasta_saida, "aug_" + arquivo)
        cv2.imwrite(caminho_saida, imagem_aumentada)

        print(f" Gerada: {caminho_saida}")


# ===== EXECUÇÃO =====
print("\n▶ Processando RGFRENTE...")
processar_pasta(PASTA_FRENTE, PASTA_FRENTE_SAIDA)

print("\n▶ Processando RGTRAS...")
processar_pasta(PASTA_TRAS, PASTA_TRAS_SAIDA)

print("\n Todas as imagens de frente e trás foram aumentadas com sucesso!")

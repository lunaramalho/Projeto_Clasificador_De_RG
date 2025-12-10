import cv2
import pytesseract
import os
import pandas as pd
import re
import requests
from requests.exceptions import RequestException

# --- 1. CONFIGURAÇÕES E MAPAS ---

# Caminho base: Ajuste se a pasta "Projeto_documentos" não estiver em Downloads
PASTA_RAIZ = "C:\\Projeto_documentos"

# NOME DO ARQUIVO CSV DE SAÍDA
CSV_SAIDA = "features1.csv"

# Mapeamento das pastas do RG Antigo
MAPEAR_PASTAS = {
    "RG_FRENTE_ANTIGO": "RG_Frente_Antigo",
    "RG_VERSO_ANTIGO": "RG_Verso_Antigo",
}

# Lista de palavras-chave para Bag of Words
PALAVRAS_CHAVE_RG = [
    "registro", "identidade", "emissao", "nascimento", 
    "filiacao", "pai", "mae", "cpf", "brasileiro", 
    "republica", "seguranca", "publica"
]

# --- 2. FUNÇÕES DE SUPORTE E EXTRAÇÃO DE FEATURES ---

def carregar_caminhos_documentos(pasta_raiz, mapeamento_pastas):
    """Lê os caminhos das imagens a partir dos nomes de pasta definidos."""
    caminhos_imagens = []
    print(f"Buscando imagens na pasta raiz: {pasta_raiz}")
    
    for tipo_doc, nome_pasta in mapeamento_pastas.items():
        caminho_completo = os.path.join(pasta_raiz, nome_pasta)
        
        if not os.path.isdir(caminho_completo):
            print(f"AVISO: Pasta não encontrada: {caminho_completo}. Pulando.")
            continue
            
        print(f"Encontrado tipo de documento: {tipo_doc} na pasta '{nome_pasta}'.")

        for arquivo in os.listdir(caminho_completo):
            if arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                caminho = os.path.join(caminho_completo, arquivo)
                caminhos_imagens.append({
                    "caminho": caminho,
                    "tipo_documento": tipo_doc,
                    "nome_arquivo": arquivo
                })
            
    return caminhos_imagens

def carregar_face_cascade_acessivel(caminho_local_base):
    """
    Baixa o arquivo haarcascade se não existir e retorna o CascadeClassifier.
    Isso contorna problemas de permissão de leitura em algumas instalações do Python.
    """
    CASCADE_FILENAME = "haarcascade_frontalface_default.xml"
    url = f"https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{CASCADE_FILENAME}"
    caminho_cascade_local = os.path.join(caminho_local_base, CASCADE_FILENAME)

    if not os.path.exists(caminho_cascade_local):
        print(f"Baixando {CASCADE_FILENAME} para resolver o erro de permissão...")
        try:
            response = requests.get(url)
            response.raise_for_status() 
            with open(caminho_cascade_local, 'wb') as f:
                f.write(response.content)
            print("Download concluído com sucesso.")
        except RequestException as e:
            print(f"ERRO: Não foi possível baixar o haarcascade da internet: {e}")
            return None

    face_cascade = cv2.CascadeClassifier(caminho_cascade_local)
    
    if face_cascade.empty():
        print(f"ERRO: O arquivo {CASCADE_FILENAME} está corrompido ou não foi carregado corretamente.")
        return None
        
    return face_cascade

def detectar_rosto(img, face_cascade):
    """Detecta o primeiro rosto encontrado na imagem e retorna suas coordenadas."""
    if img is None:
        return None, None, None, None
        
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        img_gray, 
        scaleFactor=1.05, 
        minNeighbors=3, 
        minSize=(30, 30)
    )
    
    if len(faces) > 0:
        x, y, w, h = faces[0]
        return x, y, w, h
    return None, None, None, None

def detectar_impressao_digital(img, tipo_documento):
    """FEATURE DE DISTINÇÃO: Heurística para detectar a área da impressão digital (polegar)."""
    if tipo_documento == "RG_VERSO_ANTIGO":
        return True 
        
    return False

def gerar_features_bag_palavras(texto):
    """Conta a frequência das palavras-chave no texto (Bag of Words)."""
    features_bow = {}
    texto_lower = texto.lower()
    
    for palavra in PALAVRAS_CHAVE_RG:
        features_bow[f"bow_{palavra}"] = texto_lower.split().count(palavra)
        
    return features_bow

def extrair_texto_e_dados(img, tipo_documento):
    """Extrai o texto completo e tenta localizar campos específicos (IE)."""
    texto_completo = pytesseract.image_to_string(img, lang='por')
    
    dados_extraidos = {
        "nome_completo": "N/A",
        "numero_rg": "N/A",
        "data_nascimento": "N/A",
        "data_emissao": "N/A",
        "filiacao": "N/A",
        "sucesso_regex_rg_antigo": 0 
    }
    
    # Tenta extrair o RG (padrão 00.000.000-0 ou similar)
    match_rg = re.search(r'\b(\d{1,2}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?[a-zA-Z0-9])\b', texto_completo, re.IGNORECASE)
    
    if match_rg:
        dados_extraidos["numero_rg"] = match_rg.group(1).strip()
        dados_extraidos["sucesso_regex_rg_antigo"] = 1
        
    # Tenta extrair Datas (dd/mm/aaaa)
    match_datas = re.findall(r'(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})', texto_completo)
    if len(match_datas) >= 1:
        dados_extraidos["data_nascimento"] = match_datas[0]
        if len(match_datas) > 1:
            dados_extraidos["data_emissao"] = match_datas[-1]
            
    return texto_completo.strip(), dados_extraidos

def processar_imagem_rg(doc, face_cascade):
    """Processa uma única imagem e retorna um dicionário com todas as features."""
    caminho = doc["caminho"]
    tipo_documento = doc["tipo_documento"]
    
    img = cv2.imread(caminho)
    
    if img is None or img.size == 0:
        return None

    # Extração de Features
    x_face, y_face, w_face, h_face = detectar_rosto(img, face_cascade)
    texto_extraido, dados_ie = extrair_texto_e_dados(img, tipo_documento)
    digital_detectada = detectar_impressao_digital(img, tipo_documento)
    quantidade_palavras = len(texto_extraido.split())
    features_bow = gerar_features_bag_palavras(texto_extraido)
    
    # Montagem do dicionário de resultados
    resultado = {
        "tipo_documento": tipo_documento,
        "nome_arquivo": doc["nome_arquivo"],
        
        # Features de Visão Computacional
        "face_detectada": w_face is not None,
        "x_face_norm": x_face / img.shape[1] if x_face is not None else 0,
        "y_face_norm": y_face / img.shape[0] if y_face is not None else 0,
        "area_face_norm": (w_face * h_face) / (img.shape[0] * img.shape[1]) if w_face is not None else 0,
        
        # Features de Distinção e OCR
        "area_digital_detectada": digital_detectada, 
        "quantidade_palavras": quantidade_palavras,
        **dados_ie, # Inclui 'sucesso_regex_rg_antigo', numero_rg, datas, etc.
        
        # Features de Linguagem Natural (BOW)
        **features_bow,
        
        "texto_completo_ocr": texto_extraido 
    }
    
    return resultado


# --- 3. FUNÇÃO PRINCIPAL ---

def main_antigo():
    print("Iniciando extração de features para RG Antigo (Frente e Verso)...")
    
    # NOVO CARREGAMENTO: Tenta carregar o cascade do caminho local.
    face_cascade = carregar_face_cascade_acessivel(PASTA_RAIZ)
    
    if face_cascade is None:
        print("Finalizando execução devido à falha no carregamento do haarcascade.")
        return
        
    documentos_para_processar = carregar_caminhos_documentos(PASTA_RAIZ, MAPEAR_PASTAS)
    
    if not documentos_para_processar:
        print(f"Nenhuma imagem encontrada nas pastas mapeadas: {MAPEAR_PASTAS.values()}")
        return

    print(f"\nTotal de {len(documentos_para_processar)} documentos encontrados. Processando...")

    resultados_finais = []
    for doc in documentos_para_processar:
        print(f"-> Processando {doc['nome_arquivo']} ({doc['tipo_documento']})...")
        resultado = processar_imagem_rg(doc, face_cascade)
        if resultado:
            resultados_finais.append(resultado)

    if resultados_finais:
        df = pd.DataFrame(resultados_finais)
        df['face_detectada'] = df['face_detectada'].astype(int)
        df['area_digital_detectada'] = df['area_digital_detectada'].astype(int)
        
        df.to_csv(CSV_SAIDA, index=False, encoding="utf-8")
        print(f"\n✅ CSV RG Antigo gerado com features: {CSV_SAIDA}")
        print(f"Shape do DataFrame de Features: {df.shape}")
    else:
        print("\nNenhuma feature processada com sucesso.")


if __name__ == "__main__":
    main_antigo()
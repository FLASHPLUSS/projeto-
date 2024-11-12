import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import os
import json
import hashlib
import time

app = Flask(__name__)

# Ajuste do diretório de cache para compatibilidade com o ambiente do Vercel
CACHE_DIR = '/tmp/cache/'  # Use o diretório temporário para armazenamento de cache no Vercel
CACHE_EXPIRATION_TIME = 60 * 60 * 24  # Tempo de expiração do cache em segundos (1 dia)

LINK_DROPBOX = "https://www.dropbox.com/scl/fi/y18z9sbdxiw27vtm1n84s/Titulo.txt?rlkey=fap0rg6rl4v0junalq0jjvsge&st=i26hr446&dl=1"

def gerar_nome_cache():
    return hashlib.md5("todos_titulos".encode('utf-8')).hexdigest() + '.json'

def cache_valido(nome_cache):
    if not os.path.exists(nome_cache):
        return False
    timestamp = os.path.getmtime(nome_cache)
    return (time.time() - timestamp) < CACHE_EXPIRATION_TIME

def salvar_cache(nome_cache, dados):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    with open(nome_cache, 'w') as f:
        json.dump(dados, f)

def carregar_cache(nome_cache):
    with open(nome_cache, 'r') as f:
        return json.load(f)

def baixar_titulos():
    response = requests.get(LINK_DROPBOX)
    return response.text.splitlines()

def pesquisar_filme(titulo):
    url_base = "https://www.visioncine-1.com/search.php"
    params = {'q': titulo}
    response = requests.get(url_base, params=params)
    return response.text

def extrair_informacoes(html):
    soup = BeautifulSoup(html, 'html.parser')
    titulo = soup.find('h1', class_='fw-bolder').text.strip()
    ano = soup.find('span', text=True).next_sibling.strip()
    sinopse = soup.find('p', class_='small linefive').text.strip()
    genero = [g.text.strip() for g in soup.find_all('span', text=True)]
    classificacao = soup.find('em', class_='classification').text.strip()
    capa = soup.find('div', class_='poster')['style'].split('url(')[1].split(')')[0].strip("'")
    banner = soup.find('div', class_='backImage')['style'].split('url(')[1].split(')')[0].strip("'")
    return {
        'titulo': titulo,
        'ano': ano,
        'sinopse': sinopse,
        'genero': genero,
        'classificacao': classificacao,
        'capa': capa,
        'banner': banner
    }

def obter_informacoes():
    nome_cache = os.path.join(CACHE_DIR, gerar_nome_cache())
    if cache_valido(nome_cache):
        return carregar_cache(nome_cache)

    titulos = baixar_titulos()
    filmes_info = []
    for titulo in titulos:
        html = pesquisar_filme(titulo)
        informacoes = extrair_informacoes(html)
        filmes_info.append(informacoes)

    salvar_cache(nome_cache, filmes_info)
    return filmes_info

@app.route('/api/filme', methods=['GET'])
def obter_informacoes_filmes():
    informacoes = obter_informacoes()
    return jsonify(informacoes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

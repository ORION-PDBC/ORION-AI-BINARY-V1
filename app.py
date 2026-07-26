from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True) or {}

    ativo = str(dados.get("ativo", "")).strip().upper()

    if not ativo:
        return jsonify({
            "sucesso": False,
            "erro": "Nenhum ativo foi informado."
        }), 400

    try:
        url = f"https://brapi.dev/api/quote/{ativo}"
        resposta = requests.get(url, timeout=10)

        if resposta.status_code != 200:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Não foi possível obter os dados do ativo."
            }), 502

        dados_brapi = resposta.json()

        resultados = dados_brapi.get("results", [])

        if not resultados:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Ativo não encontrado."
            }), 404

        cotacao = resultados[0]

        return jsonify({
            "sucesso": True,
            "ativo": ativo,
            "status": "cotacao_recebida",
            "nome": cotacao.get("longName"),
            "preco": cotacao.get("regularMarketPrice"),
            "variacao": cotacao.get("regularMarketChange"),
            "variacao_percentual": cotacao.get("regularMarketChangePercent"),
            "maxima": cotacao.get("regularMarketDayHigh"),
            "minima": cotacao.get("regularMarketDayLow"),
            "volume": cotacao.get("regularMarketVolume")
        })

    except requests.RequestException as erro:
        return jsonify({
            "sucesso": False,
            "ativo": ativo,
            "erro": f"Erro ao consultar a Brapi: {str(erro)}"
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

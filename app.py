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
        # Cotação atual
        url_cotacao = f"https://brapi.dev/api/quote/{ativo}"
        resposta_cotacao = requests.get(url_cotacao, timeout=10)

        if resposta_cotacao.status_code != 200:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Não foi possível obter os dados do ativo."
            }), 502

        dados_brapi = resposta_cotacao.json()
        resultados = dados_brapi.get("results", [])

        if not resultados:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Ativo não encontrado."
            }), 404

        cotacao = resultados[0]

        # Histórico intraday M5
        url_historico = (
            f"https://brapi.dev/api/quote/{ativo}"
            f"?range=1d&interval=5m"
        )

        resposta_historico = requests.get(
            url_historico,
            timeout=10
        )

        historico = []

        if resposta_historico.status_code == 200:
            dados_historico = resposta_historico.json()

            resultados_historico = dados_historico.get(
                "results",
                []
            )

            if resultados_historico:
                historico = resultados_historico[0].get(
                    "historicalDataPrice",
                    []
                )

        return jsonify({
            "sucesso": True,
            "ativo": ativo,
            "status": "cotacao_recebida",

            "nome": cotacao.get("longName"),
            "preco": cotacao.get("regularMarketPrice"),
            "variacao": cotacao.get("regularMarketChange"),
            "variacao_percentual": cotacao.get(
                "regularMarketChangePercent"
            ),
            "maxima": cotacao.get("regularMarketDayHigh"),
            "minima": cotacao.get("regularMarketDayLow"),
            "volume": cotacao.get("regularMarketVolume"),

            "timeframe": "5m",
            "historico": historico
        })

    except requests.RequestException as erro:
        return jsonify({
            "sucesso": False,
            "ativo": ativo,
            "erro": f"Erro ao consultar a Brapi: {str(erro)}"
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

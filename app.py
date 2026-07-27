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
        # =========================
        # COTAÇÃO ATUAL
        # =========================

        url_cotacao = (
            f"https://brapi.dev/api/quote/{ativo}"
        )

        resposta_cotacao = requests.get(
            url_cotacao,
            timeout=10
        )

        if resposta_cotacao.status_code != 200:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": (
                    "Não foi possível obter "
                    "os dados do ativo."
                )
            }), 502

        dados_brapi = resposta_cotacao.json()

        resultados = dados_brapi.get(
            "results",
            []
        )

        if not resultados:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Ativo não encontrado."
            }), 404

        cotacao = resultados[0]


        # =========================
        # HISTÓRICO M5
        # =========================

        url_historico = (
            f"https://brapi.dev/api/quote/{ativo}"
            f"?range=1d&interval=5m"
        )

        resposta_historico = requests.get(
            url_historico,
            timeout=10
        )

        historico = []

        status_historico = (
            resposta_historico.status_code
        )

        erro_historico = None

        campos_historico = []


        if resposta_historico.status_code == 200:

            dados_historico = (
                resposta_historico.json()
            )

            resultados_historico = (
                dados_historico.get(
                    "results",
                    []
                )
            )


            if resultados_historico:

                # Mostra quais campos a Brapi
                # realmente devolveu.
                campos_historico = list(
                    resultados_historico[0].keys()
                )

                historico = (
                    resultados_historico[0].get(
                        "historicalDataPrice",
                        []
                    )
                )


        else:

            try:

                erro_historico = (
                    resposta_historico.json()
                )

            except ValueError:

                erro_historico = (
                    resposta_historico.text
                )


        # =========================
        # DIAGNÓSTICO DOS CANDLES
        # =========================

        quantidade_candles = len(
            historico
        )

        primeiro_candle = (
            historico[0]
            if historico
            else None
        )

        ultimo_candle = (
            historico[-1]
            if historico
            else None
        )

        primeiro_timestamp = (
            primeiro_candle.get("date")
            if primeiro_candle
            else None
        )

        ultimo_timestamp = (
            ultimo_candle.get("date")
            if ultimo_candle
            else None
        )


        # =========================
        # RESPOSTA
        # =========================

        return jsonify({

            "sucesso": True,

            "ativo": ativo,

            "status": "cotacao_recebida",

            "nome": cotacao.get(
                "longName"
            ),

            "preco": cotacao.get(
                "regularMarketPrice"
            ),

            "variacao": cotacao.get(
                "regularMarketChange"
            ),

            "variacao_percentual": cotacao.get(
                "regularMarketChangePercent"
            ),

            "maxima": cotacao.get(
                "regularMarketDayHigh"
            ),

            "minima": cotacao.get(
                "regularMarketDayLow"
            ),

            "volume": cotacao.get(
                "regularMarketVolume"
            ),

            "timeframe": "5m",

            "historico": historico,

            "quantidade_candles":
                quantidade_candles,

            "campos_historico":
                campos_historico,

            "primeiro_timestamp":
                primeiro_timestamp,

            "ultimo_timestamp":
                ultimo_timestamp,

            "status_historico":
                status_historico,

            "erro_historico":
                erro_historico
        })


    except requests.RequestException as erro:

        return jsonify({

            "sucesso": False,

            "ativo": ativo,

            "erro": (
                f"Erro ao consultar a Brapi: "
                f"{str(erro)}"
            )

        }), 502


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

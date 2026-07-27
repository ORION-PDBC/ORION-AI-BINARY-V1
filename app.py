from flask import Flask, render_template, request, jsonify
import requests
import os

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
        # ==============================
        # TOKEN DA BRAPI
        # ==============================

        token = os.environ.get("BRAPI_TOKEN")

        if not token:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "BRAPI_TOKEN não está configurado no servidor."
            }), 500

        headers = {
            "Authorization": f"Bearer {token}"
        }


        # ==============================
        # COTAÇÃO ATUAL
        # ==============================

        url_cotacao = f"https://brapi.dev/api/quote/{ativo}"

        resposta_cotacao = requests.get(
            url_cotacao,
            timeout=10
        )

        if resposta_cotacao.status_code != 200:
            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Não foi possível obter os dados do ativo."
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


        # ==============================
        # HISTÓRICO INTRADAY M5
        # ==============================

        url_historico = (
            "https://brapi.dev/api/v2/stocks/historical"
        )

        parametros_historico = {
            "symbols": ativo,
            "range": "5d",
            "interval": "5m"
        }

        resposta_historico = requests.get(
            url_historico,
            params=parametros_historico,
            headers=headers,
            timeout=10
        )


        historico = []

        erro_historico = None


        # ==============================
        # DIAGNÓSTICO DA BRAPI
        # ==============================

        status_historico = resposta_historico.status_code

        if resposta_historico.status_code == 200:

            try:
                dados_historico = resposta_historico.json()

                resultados_historico = dados_historico.get(
                    "results",
                    []
                )

                if resultados_historico:

                    dados_ativo = resultados_historico[0].get(
                        "data",
                        {}
                    )

                    historico = dados_ativo.get(
                        "historicalDataPrice",
                        []
                    )

            except ValueError:

                erro_historico = (
                    "A Brapi respondeu, mas não retornou "
                    "JSON válido."
                )

        else:

            try:
                resposta_erro = resposta_historico.json()

                erro_historico = resposta_erro

            except ValueError:

                erro_historico = resposta_historico.text


        quantidade_candles = len(historico)


        # ==============================
        # RESPOSTA DO ORION
        # ==============================

    # Diagnóstico do histórico M5
    primeiro_candle = historico[0] if historico else None
    ultimo_candle = historico[-1] if historico else None

    quantidade_candles = len(historico)

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

            "status_historico": status_historico,

            "quantidade_candles": quantidade_candles,

            "historico": historico,
        
            "quantidade_candles": quantidade_candles,
            "primeiro_timestamp": primeiro_timestamp,
            "ultimo_timestamp": ultimo_timestamp

            "erro_historico": erro_historico
        })


    except requests.RequestException as erro:

        return jsonify({

            "sucesso": False,

            "ativo": ativo,

            "erro": (
                "Erro ao consultar a Brapi: "
                f"{str(erro)}"
            )

        }), 502


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

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

    ativo = str(
        dados.get("ativo", "")
    ).strip().upper()

    if not ativo:
        return jsonify({
            "sucesso": False,
            "erro": "Nenhum ativo foi informado."
        }), 400

    try:
        # ==================================================
        # TOKEN DA BRAPI
        # ==================================================

        token = os.environ.get(
            "BRAPI_TOKEN"
        )

        headers = {}

        if token:
            headers["Authorization"] = (
                f"Bearer {token}"
            )


        # ==================================================
        # COTAÇÃO ATUAL
        # ==================================================

        url_cotacao = (
            "https://brapi.dev/api/v2/stocks/quote"
        )

        resposta_cotacao = requests.get(
            url_cotacao,
            headers=headers,
            params={
                "symbols": ativo
            },
            timeout=10
        )


        if resposta_cotacao.status_code != 200:

            try:
                erro_cotacao = (
                    resposta_cotacao.json()
                )
            except ValueError:
                erro_cotacao = (
                    resposta_cotacao.text
                )

            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": (
                    "Não foi possível obter "
                    "a cotação do ativo."
                ),
                "status_cotacao":
                    resposta_cotacao.status_code,
                "resposta_cotacao":
                    erro_cotacao
            }), 502


        dados_cotacao = (
            resposta_cotacao.json()
        )

        resultados_cotacao = (
            dados_cotacao.get(
                "results",
                []
            )
        )


        if not resultados_cotacao:

            return jsonify({
                "sucesso": False,
                "ativo": ativo,
                "erro": "Ativo não encontrado."
            }), 404


        cotacao = (
            resultados_cotacao[0]
        )


        # ==================================================
        # HISTÓRICO M5 — API V2
        # ==================================================

        url_historico = (
            "https://brapi.dev/api/v2/stocks/historical"
        )


        resposta_historico = requests.get(
            url_historico,
            headers=headers,
            params={
                "symbols": ativo,
                "range": "1d",
                "interval": "5m",
                "sortOrder": "asc"
            },
            timeout=10
        )


        historico = []

        status_historico = (
            resposta_historico.status_code
        )

        erro_historico = None

        campos_historico = []

        quantidade_historico_brapi = 0

        primeiro_item_historico = None


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

                resultado_historico = (
                    resultados_historico[0]
                )


                campos_historico = list(
                    resultado_historico.keys()
                )


                # Na API V2 os candles ficam
                # dentro de results[0].data
                dados_series = (
                    resultado_historico.get(
                        "data",
                        {}
                    )
                )


                if isinstance(
                    dados_series,
                    dict
                ):

                    historico_brapi = (
                        dados_series.get(
                            "historicalDataPrice",
                            []
                        )
                    )

                else:

                    historico_brapi = []


                if historico_brapi is None:

                    historico_brapi = []


                quantidade_historico_brapi = len(
                    historico_brapi
                )


                if (
                    quantidade_historico_brapi > 0
                ):

                    primeiro_item_historico = (
                        historico_brapi[0]
                    )


                historico = (
                    historico_brapi
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


        # ==================================================
        # DIAGNÓSTICO
        # ==================================================

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


        # ==================================================
        # RESPOSTA AO ORION
        # ==================================================

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

            "quantidade_historico_brapi":
                quantidade_historico_brapi,

            "primeiro_item_historico":
                primeiro_item_historico,

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


    except Exception as erro:

        return jsonify({

            "sucesso": False,

            "ativo": ativo,

            "erro": (
                f"Erro interno no servidor: "
                f"{str(erro)}"
            )

        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

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

        token = os.environ.get("BRAPI_TOKEN")

        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"


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
            timeout=15
        )

        status_cotacao = (
            resposta_cotacao.status_code
        )

        try:
            dados_cotacao = (
                resposta_cotacao.json()
            )
        except ValueError:
            dados_cotacao = {}


        # ==================================================
        # DIAGNÓSTICO DA COTAÇÃO
        # ==================================================

        resultados_cotacao = (
            dados_cotacao.get(
                "results",
                []
            )
            if isinstance(
                dados_cotacao,
                dict
            )
            else []
        )


        cotacao = {}

        if (
            isinstance(
                resultados_cotacao,
                list
            )
            and len(resultados_cotacao) > 0
            and isinstance(
                resultados_cotacao[0],
                dict
            )
        ):

        cotacao = (
            resultados_cotacao[0]
        )

        print("==========================================")
        print("DEBUG COTAÇÃO BRAPI")
        print("==========================================")
        print("JSON COMPLETO DA COTAÇÃO:")
        print(dados_cotacao)
        print("==========================================")
        print("RESULTADOS[0]:")
        print(cotacao)
        print("==========================================")


        # ==================================================
        # HISTÓRICO M5
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
            timeout=15
        )

        status_historico = (
            resposta_historico.status_code
        )

        erro_historico = None

        historico = []

        campos_historico = []

        quantidade_historico_brapi = 0

        primeiro_item_historico = None


        try:

            dados_historico = (
                resposta_historico.json()
            )

        except ValueError:

            dados_historico = {}


        resultados_historico = (
            dados_historico.get(
                "results",
                []
            )
            if isinstance(
                dados_historico,
                dict
            )
            else []
        )


        if (
            isinstance(
                resultados_historico,
                list
            )
            and len(resultados_historico) > 0
            and isinstance(
                resultados_historico[0],
                dict
            )
        ):

            resultado_historico = (
                resultados_historico[0]
            )

            campos_historico = list(
                resultado_historico.keys()
            )

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


            if not isinstance(
                historico_brapi,
                list
            ):

                historico_brapi = []


            quantidade_historico_brapi = (
                len(historico_brapi)
            )


            if quantidade_historico_brapi > 0:

                primeiro_item_historico = (
                    historico_brapi[0]
                )


            # ==================================================
            # NORMALIZAÇÃO DOS CANDLES
            # ==================================================

            for candle in historico_brapi:

                if not isinstance(
                    candle,
                    dict
                ):
                    continue

                try:

                    timestamp = int(
                        candle.get("date")
                    )

                    abertura = float(
                        candle.get("open")
                    )

                    maxima = float(
                        candle.get("high")
                    )

                    minima = float(
                        candle.get("low")
                    )

                    fechamento = float(
                        candle.get("close")
                    )

                    volume = candle.get(
                        "volume"
                    )

                    if volume is not None:
                        volume = float(volume)

                except (
                    TypeError,
                    ValueError
                ):

                    continue


                historico.append({

                    "date":
                        timestamp,

                    "open":
                        abertura,

                    "high":
                        maxima,

                    "low":
                        minima,

                    "close":
                        fechamento,

                    "volume":
                        volume

                })


        else:

            if status_historico != 200:

                erro_historico = (
                    dados_historico
                )


        # ==================================================
        # ORDENAÇÃO
        # ==================================================

        historico.sort(
            key=lambda candle:
                candle["date"]
        )


        # ==================================================
        # DIAGNÓSTICO DO HISTÓRICO
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
        # RETORNO
        # ==================================================

        return jsonify({

            "sucesso": True,

            "ativo": ativo,

            "status": "cotacao_recebida",

            # ==============================================
            # COTAÇÃO
            # ==============================================

            "nome":
                cotacao.get("longName")
                or cotacao.get("shortName")
                or cotacao.get("name"),

            "preco":
                cotacao.get("regularMarketPrice")
                or cotacao.get("price")
                or cotacao.get("regularMarketPreviousClose"),

            "variacao":
                cotacao.get("regularMarketChange")
                or cotacao.get("change"),

            "variacao_percentual":
                cotacao.get("regularMarketChangePercent")
                or cotacao.get("changePercent"),

            "maxima":
                cotacao.get("regularMarketDayHigh")
                or cotacao.get("dayHigh")
                or cotacao.get("high"),

            "minima":
                cotacao.get("regularMarketDayLow")
                or cotacao.get("dayLow")
                or cotacao.get("low"),

            "volume":
                cotacao.get("regularMarketVolume")
                or cotacao.get("volume"),

            # ==============================================
            # HISTÓRICO
            # ==============================================

            "timeframe":
                "5m",

            "historico":
                historico,

            "quantidade_candles":
                quantidade_candles,

            "status_cotacao":
                status_cotacao,

            "campos_cotacao":
                list(cotacao.keys()),

            "resposta_cotacao":
                dados_cotacao,

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


    # ==================================================
    # ERRO DE REDE
    # ==================================================

    except requests.RequestException as erro:

        return jsonify({

            "sucesso": False,

            "ativo": ativo,

            "erro":
                f"Erro ao consultar a Brapi: {str(erro)}"

        }), 502


    # ==================================================
    # ERRO INTERNO
    # ==================================================

    except Exception as erro:

        return jsonify({

            "sucesso": False,

            "ativo": ativo,

            "erro":
                f"Erro interno no servidor: {str(erro)}"

        }), 500


# ======================================================
# EXECUÇÃO
# ======================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

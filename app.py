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


        # ==================================================
        # LEITURA DA RESPOSTA DA COTAÇÃO
        # ==================================================

        try:

            dados_cotacao = (
                resposta_cotacao.json()
            )

        except ValueError:

            dados_cotacao = {
                "resposta_texto":
                    resposta_cotacao.text
            }


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


        cotacao = (
            resultados_cotacao[0]
            if resultados_cotacao
            else {}
        )


        # ==================================================
        # DIAGNÓSTICO COMPLETO DA COTAÇÃO
        # ==================================================

        campos_cotacao = []

        if isinstance(
            cotacao,
            dict
        ):

            campos_cotacao = list(
                cotacao.keys()
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


        # ==================================================
        # LEITURA DO HISTÓRICO
        # ==================================================

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


                if quantidade_historico_brapi > 0:

                    primeiro_item_historico = (
                        historico_brapi[0]
                    )


                # ==================================================
                # NORMALIZAÇÃO DO HISTÓRICO M5
                # ==================================================

                historico_normalizado = []

                for candle in historico_brapi:

                    if not isinstance(
                        candle,
                        dict
                    ):
                        continue


                    timestamp = candle.get(
                        "date"
                    )

                    abertura = candle.get(
                        "open"
                    )

                    maxima = candle.get(
                        "high"
                    )

                    minima = candle.get(
                        "low"
                    )

                    fechamento = candle.get(
                        "close"
                    )

                    volume = candle.get(
                        "volume"
                    )


                    if timestamp is None:
                        continue

                    if abertura is None:
                        continue

                    if maxima is None:
                        continue

                    if minima is None:
                        continue

                    if fechamento is None:
                        continue


                    try:

                        timestamp = int(
                            timestamp
                        )

                        abertura = float(
                            abertura
                        )

                        maxima = float(
                            maxima
                        )

                        minima = float(
                            minima
                        )

                        fechamento = float(
                            fechamento
                        )

                        if volume is not None:

                            volume = float(
                                volume
                            )

                    except (
                        TypeError,
                        ValueError
                    ):

                        continue


                    candle_normalizado = {

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
                    }


                    historico_normalizado.append(
                        candle_normalizado
                    )


                historico_normalizado.sort(
                    key=lambda candle:
                        candle["date"]
                )


                historico = (
                    historico_normalizado
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


        primeiro_open = (
            primeiro_candle.get("open")
            if primeiro_candle
            else None
        )

        primeiro_high = (
            primeiro_candle.get("high")
            if primeiro_candle
            else None
        )

        primeiro_low = (
            primeiro_candle.get("low")
            if primeiro_candle
            else None
        )

        primeiro_close = (
            primeiro_candle.get("close")
            if primeiro_candle
            else None
        )

        primeiro_volume = (
            primeiro_candle.get("volume")
            if primeiro_candle
            else None
        )


        ultimo_open = (
            ultimo_candle.get("open")
            if ultimo_candle
            else None
        )

        ultimo_high = (
            ultimo_candle.get("high")
            if ultimo_candle
            else None
        )

        ultimo_low = (
            ultimo_candle.get("low")
            if ultimo_candle
            else None
        )

        ultimo_close = (
            ultimo_candle.get("close")
            if ultimo_candle
            else None
        )

        ultimo_volume = (
            ultimo_candle.get("volume")
            if ultimo_candle
            else None
        )


        # ==================================================
        # VALIDAÇÃO DA ORDEM CRONOLÓGICA
        # ==================================================

        historico_em_ordem = True

        if len(historico) > 1:

            for i in range(
                1,
                len(historico)
            ):

                timestamp_anterior = (
                    historico[i - 1]["date"]
                )

                timestamp_atual = (
                    historico[i]["date"]
                )

                if timestamp_atual < timestamp_anterior:

                    historico_em_ordem = False

                    break


        # ==================================================
        # INTERVALOS ENTRE CANDLES
        # ==================================================

        intervalo_esperado_segundos = (
            5 * 60
        )

        quantidade_intervalos_validos = 0

        quantidade_intervalos_incorretos = 0

        maior_intervalo_segundos = 0


        if len(historico) > 1:

            for i in range(
                1,
                len(historico)
            ):

                anterior = (
                    historico[i - 1]["date"]
                )

                atual = (
                    historico[i]["date"]
                )

                intervalo = (
                    atual - anterior
                )


                if intervalo == (
                    intervalo_esperado_segundos
                ):

                    quantidade_intervalos_validos += 1

                else:

                    quantidade_intervalos_incorretos += 1


                if intervalo > maior_intervalo_segundos:

                    maior_intervalo_segundos = (
                        intervalo
                    )


        # ==================================================
        # RESPOSTA AO ORION
        # ==================================================

        return jsonify({

            "sucesso":
                True,

            "ativo":
                ativo,

            "status":
                "cotacao_recebida",


            # ==================================================
            # DIAGNÓSTICO DA COTAÇÃO
            # ==================================================

            "status_cotacao":
                resposta_cotacao.status_code,

            "campos_cotacao":
                campos_cotacao,

            "resposta_cotacao_completa":
                cotacao,


            # ==================================================
            # COTAÇÃO NORMALIZADA ATUAL
            # ==================================================

            "nome":
                cotacao.get(
                    "longName"
                ),

            "preco":
                cotacao.get(
                    "regularMarketPrice"
                ),

            "variacao":
                cotacao.get(
                    "regularMarketChange"
                ),

            "variacao_percentual":
                cotacao.get(
                    "regularMarketChangePercent"
                ),

            "maxima":
                cotacao.get(
                    "regularMarketDayHigh"
                ),

            "minima":
                cotacao.get(
                    "regularMarketDayLow"
                ),

            "volume":
                cotacao.get(
                    "regularMarketVolume"
                ),


            # ==================================================
            # HISTÓRICO
            # ==================================================

            "timeframe":
                "5m",

            "historico":
                historico,

            "quantidade_candles":
                quantidade_candles,

            "campos_historico":
                campos_historico,

            "quantidade_historico_brapi":
                quantidade_historico_brapi,

            "primeiro_item_historico":
                primeiro_item_historico,


            # ==================================================
            # TIMESTAMPS
            # ==================================================

            "primeiro_timestamp":
                primeiro_timestamp,

            "ultimo_timestamp":
                ultimo_timestamp,


            # ==================================================
            # PRIMEIRO CANDLE
            # ==================================================

            "primeiro_open":
                primeiro_open,

            "primeiro_high":
                primeiro_high,

            "primeiro_low":
                primeiro_low,

            "primeiro_close":
                primeiro_close,

            "primeiro_volume":
                primeiro_volume,


            # ==================================================
            # ÚLTIMO CANDLE
            # ==================================================

            "ultimo_open":
                ultimo_open,

            "ultimo_high":
                ultimo_high,

            "ultimo_low":
                ultimo_low,

            "ultimo_close":
                ultimo_close,

            "ultimo_volume":
                ultimo_volume,


            # ==================================================
            # VALIDAÇÕES
            # ==================================================

            "historico_em_ordem":
                historico_em_ordem,

            "intervalo_esperado_segundos":
                intervalo_esperado_segundos,

            "quantidade_intervalos_validos":
                quantidade_intervalos_validos,

            "quantidade_intervalos_incorretos":
                quantidade_intervalos_incorretos,

            "maior_intervalo_segundos":
                maior_intervalo_segundos,


            # ==================================================
            # STATUS DA BRAPI
            # ==================================================

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

            "sucesso":
                False,

            "ativo":
                ativo,

            "erro":
                (
                    f"Erro ao consultar a Brapi: "
                    f"{str(erro)}"
                )

        }), 502


    # ==================================================
    # ERRO INTERNO
    # ==================================================

    except Exception as erro:

        return jsonify({

            "sucesso":
                False,

            "ativo":
                ativo,

            "erro":
                (
                    f"Erro interno no servidor: "
                    f"{str(erro)}"
                )

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

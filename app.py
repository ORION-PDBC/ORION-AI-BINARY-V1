from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)


def obter_cotacao(ativo):
    ativo = ativo.strip().upper()

    if not ativo:
        raise ValueError("Informe um ativo.")

    # Converte ações brasileiras para o formato do Yahoo Finance
    ticker = ativo
    if not ticker.endswith(".SA"):
        ticker = f"{ticker}.SA"

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    params = {
        "range": "5d",
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,splits"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resposta = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if resposta.status_code != 200:
        raise ValueError(
            f"Não foi possível consultar o ativo {ativo}."
        )

    dados = resposta.json()

    resultado = dados.get("chart", {}).get("result")

    if not resultado:
        raise ValueError(
            f"Ativo {ativo} não encontrado."
        )

    resultado = resultado[0]

    meta = resultado.get("meta", {})

    preco = meta.get("regularMarketPrice")

    if preco is None:
        precos = (
            resultado
            .get("indicators", {})
            .get("quote", [{}])[0]
            .get("close", [])
        )

        precos_validos = [
            valor for valor in precos
            if valor is not None
        ]

        if not precos_validos:
            raise ValueError(
                f"Não foi possível obter o preço de {ativo}."
            )

        preco = precos_validos[-1]

    # Tenta obter preço anterior
    precos = (
        resultado
        .get("indicators", {})
        .get("quote", [{}])[0]
        .get("close", [])
    )

    precos_validos = [
        valor for valor in precos
        if valor is not None
    ]

    variacao = 0.0

    if len(precos_validos) >= 2:
        anterior = precos_validos[-2]

        if anterior:
            variacao = (
                (preco - anterior)
                / anterior
            ) * 100

    return {
        "ativo": ativo,
        "ticker": ticker,
        "preco": round(float(preco), 2),
        "variacao": round(float(variacao), 2),
        "timestamp": datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analisar", methods=["POST"])
def analisar():
    try:
        dados = request.get_json(silent=True) or {}

        ativo = dados.get("ativo", "")

        if not ativo:
            return jsonify({
                "ok": False,
                "erro": "Informe o código do ativo."
            }), 400

        resultado = obter_cotacao(ativo)

        # Neste momento o sinal é apenas uma indicação
        # baseada na variação diária.
        # A lógica ORION propriamente dita será adicionada
        # posteriormente.
        variacao = resultado["variacao"]

        if variacao > 1:
            sinal = "ALTA"
            descricao = "Movimento positivo no período analisado."
        elif variacao < -1:
            sinal = "BAIXA"
            descricao = "Movimento negativo no período analisado."
        else:
            sinal = "NEUTRO"
            descricao = "Movimento próximo da estabilidade."

        resultado["sinal"] = sinal
        resultado["descricao"] = descricao
        resultado["ok"] = True

        return jsonify(resultado)

    except ValueError as erro:
        return jsonify({
            "ok": False,
            "erro": str(erro)
        }), 400

    except requests.RequestException:
        return jsonify({
            "ok": False,
            "erro": "Falha de comunicação com o provedor de mercado."
        }), 502

    except Exception as erro:
        print("ERRO:", erro)

        return jsonify({
            "ok": False,
            "erro": "Erro interno ao realizar a análise."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )

from flask import Flask, render_template, request, jsonify

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

    return jsonify({
        "sucesso": True,
        "ativo": ativo,
        "status": "recebido",
        "mensagem": f"Ativo {ativo} recebido para análise."
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

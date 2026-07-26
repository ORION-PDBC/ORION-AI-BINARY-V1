document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#analysisForm");
    const input = document.querySelector("#assetCode");
    const analysisText = document.querySelector("#analysisText");
    const resultPanel = document.querySelector("#resultPanel");
    const status = document.querySelector("#status");

    if (!form) {
        console.warn("ORION: formulário de análise não encontrado.");
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const assetCode = input ? input.value.trim() : "";

        if (!assetCode) {
            if (analysisText) {
                analysisText.textContent =
                    "Informe o código do ativo para iniciar a análise.";
            }
            return;
        }

        if (status) {
            status.textContent = "ANALISANDO...";
        }

        if (resultPanel) {
            resultPanel.classList.add("loading");
        }

        if (analysisText) {
            analysisText.textContent =
                "O ORION está processando os dados do ativo...";
        }

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    asset: assetCode
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Não foi possível concluir a análise."
                );
            }

            if (analysisText) {
                analysisText.textContent =
                    data.analysis ||
                    "Análise concluída. Nenhum detalhe adicional foi retornado.";
            }

            if (status) {
                status.textContent = "ANÁLISE CONCLUÍDA";
            }
        } catch (error) {
            console.error("ORION:", error);

            if (analysisText) {
                analysisText.textContent =
                    "Não foi possível concluir a análise neste momento.";
            }

            if (status) {
                status.textContent = "ERRO NA ANÁLISE";
            }
        } finally {
            if (resultPanel) {
                resultPanel.classList.remove("loading");
            }
        }
    });
});

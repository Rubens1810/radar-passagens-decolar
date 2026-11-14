import os
import httpx


def send_discord_alert(flight: dict, avg_price: float | None = None):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL não encontrado no arquivo .env")

    description = (
        f"**Trecho:** `{flight['route']}`\n"
        f"**Data:** `{flight['departure_date']}`\n"
        f"**Companhia:** `{flight['airline']}`\n"
        f"**Menor Preço:** **{flight['currency']} {flight['price']:.2f}**\n"
        f"🔗 [Abrir busca na Decolar]({flight['url']})"
    )

    if avg_price and avg_price > flight["price"]:
        discount = ((avg_price - flight["price"]) / avg_price) * 100
        description += f"\n📉 **Economia de {discount:.1f}%** (Média: {flight['currency']} {avg_price:.2f})"

    payload = {
        "username": "Radar de Passagens ✈️",
        "embeds": [
            {
                "title": "🚨 Cotação Encontrada na Decolar!",
                "description": description,
                "color": 3066993,
            }
        ],
    }

    response = httpx.post(webhook_url, json=payload, timeout=10.0)
    response.raise_for_status()
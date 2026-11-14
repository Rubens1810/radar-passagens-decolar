import os
import httpx


def send_discord_alert(flight: dict, avg_price: float | None = None, hit_target: bool = False):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL não encontrado no arquivo .env")

    title = "🔥 PREÇO-ALVO ATINGIDO!" if hit_target else "🚨 Oportunidade de Passagem Encontrada!"
    color = 15844367 if hit_target else 3066993

    seller = flight.get("seller", "Decolar / Companhia Aérea")

    description = (
        f"**Viagem:** `{flight['trip_name']}`\n"
        f"**Melhor Trecho:** `{flight['route']}`\n"
        f"**Data:** `{flight['departure_date']}`\n"
        f"**Companhia:** `{flight['airline']}`\n"
        f"**Menor Preço:** **{flight['currency']} {flight['price']:.2f}**\n"
        f"**Comprar via:** `{seller}`\n"
    )

    if flight.get("target_price"):
        description += f"🎯 **Seu Preço-Alvo:** {flight['currency']} {flight['target_price']:.2f}\n"

    if avg_price and avg_price > flight["price"]:
        discount = ((avg_price - flight["price"]) / avg_price) * 100
        description += f"📉 **Economia de {discount:.1f}%** (Média histórica: {flight['currency']} {avg_price:.2f})\n"

    description += f"🛒 **[Comprar passagem diretamente ({seller})]({flight['url']})**"

    payload = {
        "username": "Radar de Passagens ✈️",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
            }
        ],
    }

    response = httpx.post(webhook_url, json=payload, timeout=10.0)
    response.raise_for_status()